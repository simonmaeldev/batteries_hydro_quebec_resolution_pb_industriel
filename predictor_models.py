from lifelines import *
from sklearn.model_selection import train_test_split
from sklearn.model_selection import KFold
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

# How to use the code
#
# setup the pandas dataframe that will contain the data.
# pandas dataframe, with columns: 'ncycles' (maximum between the number of cycles at which death occured,
#                                            or number of cycles the battery was ran at) , 'censoring' (0 if no death, 1 if death recorded)
#                                            any number of  columns for other predictors
#                                            and
#                              with rows: one per battery
#
# Then run the following lines:
# import predictor_models as pm
# predictor = pm.predictor_models(yourdf)
# results = predictor.extract_models_mae()
# print(results)


class predictor_models:
    """
    params
    :indata pandas dataframe, with columns: 'ncycles' (maximum between the number of cycles at which death occured,
                                            or number of cycles the battery was ran at) , 'censoring' (0 if no death, 1 if death recorded)
                                            any number of  columns for other predictors
                                            and
                              with rows: one per battery
    """

    def __init__(self, indata):
        self.indata = indata
        # BUG (qualité / logique): test_size=0.9 signifie 90% en validation, 10% en train — probablement inversé.
        # De plus, train_data et valid_data ne sont jamais réutilisés nulle part dans la classe (les folds prennent le relais).
        # FIX: commenté — ligne sans effet sur l'exécution. À discuter avec l'auteur (supprimer ou corriger test_size=0.1).
        # self.train_data, self.valid_data = train_test_split(self.indata, test_size=0.9)
        # BUG (qualité): create_folds() assigne self.folds en interne mais ne retourne rien (retourne None implicitement).
        # self.fold (sans 's') valait donc None et n'était jamais réutilisé — c'est self.folds (avec 's') qui est utilisé partout.
        # FIX: suppression de l'assignation inutile.
        self.create_folds()

        self.xtensor = torch.tensor(
            indata.drop(["ncycles", "censoring"], axis=1).values, dtype=torch.float32
        )
        self.ytensor = torch.tensor(indata["ncycles"].values, dtype=torch.float32)
        self.ctensor = torch.tensor(indata["censoring"].values, dtype=torch.float32)

        self.modeldict = {
            "weibul": self.fit_weibull,
            "gengamma": self.fit_gengamma,
            "lognorm": self.fit_lognorm,
            "neuralnet1layer": self.fit_neuralnet1,
            "neuralnet2layer": self.fit_neuralnet2,
        }

    def loss_fx(self, ypred, ytrue, censoring):
        # là ici tu peux juste utiliser censoring.
        # tu dis uncensored = 1 si censoring == 1, 0 sinon
        # censored = 1 si censoring == 0, 0 sinon, donc censored c'est !censoring
        uncensored = censoring == 1
        censored = censoring == 0

        uncensored_loss = (
            torch.mean((ypred[uncensored] - ytrue[uncensored]) ** 2)
            if uncensored.sum() > 0
            else torch.tensor(0.0)
        )

        overshoot_mask = censored & (ypred > ytrue)
        censored_loss = (
            torch.mean((ypred[overshoot_mask] - ytrue[overshoot_mask]) ** 2)
            if overshoot_mask.sum() > 0
            else torch.tensor(0.0)
        )

        return uncensored_loss + censored_loss

    def create_folds(self, nfolds=20):
        rng = np.random.default_rng(42)
        folds = np.array_split(rng.permutation(len(self.indata)), nfolds)

        self.folds = [
            (folds[i], np.concatenate([folds[j] for j in range(nfolds) if j != i]))
            for i in range(nfolds)
        ]

    def fit_weibull(self):
        mae = 0
        for ff in self.folds:
            ttrain = self.indata.iloc[ff[1]]
            tval = self.indata.iloc[ff[0]]
            ctval = tval[tval["censoring"] == 1]
            if ctval.empty:
                continue

            model = WeibullAFTFitter().fit(
                ttrain,
                duration_col="ncycles",
                event_col="censoring",
                # label="ExponentialFitter",  # paramètre inexistant sur AFTFitter (existe sur KaplanMeierFitter)
            )
            y_pred = model.predict_percentile(tval[tval["censoring"] == 1])
            y_true = ctval["ncycles"]

            mae += np.sum(abs(y_pred - y_true))

        self.weibul_model = WeibullAFTFitter().fit(
            self.indata,
            duration_col="ncycles",
            event_col="censoring",
            # label="ExponentialFitter",  # paramètre inexistant sur AFTFitter (existe sur KaplanMeierFitter)
        )

        return mae / np.sum(self.indata["censoring"])

    def fit_gengamma(self):
        # same as for fit weibul but with generalized gamma
        mae = 0
        for ff in self.folds:
            ttrain = self.indata.iloc[ff[1]]
            tval = self.indata.iloc[ff[0]]
            ctval = tval[tval["censoring"] == 1]
            if ctval.empty:
                continue

            fitter = GeneralizedGammaRegressionFitter()
            fitter._scipy_fit_method = "SLSQP"
            model = fitter.fit(
                ttrain,
                duration_col="ncycles",
                event_col="censoring",
                # label="GenGammaFitter",  # paramètre inexistant sur AFTFitter (existe sur KaplanMeierFitter)
            )
            y_pred = model.predict_percentile(tval[tval["censoring"] == 1])
            y_true = ctval["ncycles"]

            mae += np.sum(abs(y_pred - y_true))

        final_fitter = GeneralizedGammaRegressionFitter()
        final_fitter._scipy_fit_method = "SLSQP"
        self.gengamma_model = final_fitter.fit(
            self.indata,
            duration_col="ncycles",
            event_col="censoring",
            # label="GenGammaFitter",  # paramètre inexistant sur AFTFitter (existe sur KaplanMeierFitter)
        )

        return mae / np.sum(self.indata["censoring"])

    def fit_lognorm(self):
        # same as for fit weibul but with generalized gamma
        mae = 0
        for ff in self.folds:
            ttrain = self.indata.iloc[ff[1]]
            tval = self.indata.iloc[ff[0]]
            ctval = tval[tval["censoring"] == 1]
            if ctval.empty:
                continue

            model = LogNormalAFTFitter().fit(
                ttrain,
                duration_col="ncycles",
                event_col="censoring",
                # label="LogNormFitter",  # paramètre inexistant sur AFTFitter (existe sur KaplanMeierFitter)
            )
            y_pred = model.predict_percentile(tval[tval["censoring"] == 1])
            y_true = ctval["ncycles"]

            mae += np.sum(abs(y_pred - y_true))

        self.lognorm_model = LogNormalAFTFitter().fit(
            self.indata,
            duration_col="ncycles",
            event_col="censoring",
            # label="LogNormFitter",  # paramètre inexistant sur AFTFitter (existe sur KaplanMeierFitter)
        )

        return mae / np.sum(self.indata["censoring"])

    def train_net(self, model, xx, yy, cc):
        # BUG (crash): cuda n'est pas importé directement depuis torch — torch.cuda.is_available() lèvera NameError.
        # FIX: remplacer par torch.torch.cuda.is_available()
        device = "cuda" if torch.cuda.is_available() else "cpu"
        lr = 0.001
        epochs = 10

        xx = xx.to(device)
        yy = yy.to(device)
        cc = cc.to(device)
        model.to(device)

        optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=0.02)

        model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            ypred = model(xx)
            loss = self.loss_fx(ypred.squeeze(), yy, cc)
            loss.backward()
            optimizer.step()

        return model

    def fit_neuralnet1(self):
        # BUG (crash): df n'est pas défini dans ce scope — lèvera NameError à l'exécution.
        # FIX: remplacer par self.indata.shape[1] - 2 ou self.xtensor.shape[1]
        input_dim = self.xtensor.shape[1]

        class nnregr(nn.Module):
            # BUG (crash): hidden_dim déclaré dans la signature mais jamais utilisé + jamais passé à l'instanciation → TypeError.
            # FIX: hidden_dim=1 par défaut (comportement identique), utilisé dans Linear.
            def __init__(self, input_dim, hidden_dim=1):
                super(nnregr, self).__init__()
                self.lin1 = nn.Linear(input_dim, hidden_dim)

            def forward(self, x):
                return F.relu(self.lin1(x))

        # BUG (crash): même cause que train_net — cuda non importé directement.
        # FIX: torch.torch.cuda.is_available()
        device = "cuda" if torch.cuda.is_available() else "cpu"

        ypred = torch.empty(0)
        ytrue = torch.empty(0)
        cens = torch.empty(0)

        for ff in self.folds:
            tx = self.xtensor[ff[1]]
            tc = self.ctensor[ff[1]]
            ty = self.ytensor[ff[1]]

            vx = self.xtensor[ff[0]]
            vc = self.ctensor[ff[0]]
            vy = self.ytensor[ff[0]]

            model = nnregr(input_dim)

            trained_m = self.train_net(model, tx, ty, tc)

            trained_m.eval()
            with torch.no_grad():
                # BUG (crash): .to('cpu') est appelé sur le tuple (ypred, ...) et non sur le tenseur retourné par le modèle.
                # Cause: la parenthèse fermante de torch.cat est mal placée — elle englobe le tuple au lieu de le fermer avant .to().
                # FIX: torch.cat((ypred, trained_m(vx.to(device)).to('cpu')), 0)
                ypred = torch.cat((ypred, trained_m(vx.to(device)).to("cpu")), 0)
                ytrue = torch.cat((ytrue, vy), 0)
                cens = torch.cat((cens, vc), 0)

        with torch.no_grad():
            mask = cens == 1
            # np.sum(abs(ypred[mask] - ytrue[mask]))  # BUG (qualité): résultat calculé mais jamais assigné — code mort.
            return torch.mean(abs(ypred[mask] - ytrue[mask]))

    def fit_neuralnet2(self):
        # BUG (crash): df n'est pas défini dans ce scope — lèvera NameError à l'exécution.
        # FIX: remplacer par self.indata.shape[1] - 2 ou self.xtensor.shape[1]
        input_dim = self.xtensor.shape[1]
        hidden_dim = np.floor(input_dim / 4).astype(int)
        if hidden_dim < 2:
            hidden_dim = 2

        class nnregr(nn.Module):
            def __init__(self, input_dim, hidden_dim):
                super(nnregr, self).__init__()
                self.lin1 = nn.Linear(input_dim, hidden_dim)
                self.lin2 = nn.Linear(hidden_dim, 1)
                self.drop = nn.Dropout(0.2)

            def forward(self, x):
                x = F.relu(self.lin1(x))
                x = self.drop(x)
                return F.relu(self.lin2(x))

        # BUG (crash): même cause que train_net — cuda non importé directement.
        # FIX: torch.torch.cuda.is_available()
        device = "cuda" if torch.cuda.is_available() else "cpu"

        ypred = torch.empty(0)
        ytrue = torch.empty(0)
        cens = torch.empty(0)

        for ff in self.folds:
            tx = self.xtensor[ff[1]]
            tc = self.ctensor[ff[1]]
            ty = self.ytensor[ff[1]]

            vx = self.xtensor[ff[0]]
            vc = self.ctensor[ff[0]]
            vy = self.ytensor[ff[0]]

            # BUG (crash): nnregr.__init__ requiert (input_dim, hidden_dim) mais hidden_dim n'était pas passé ici.
            # hidden_dim est pourtant calculé quelques lignes au-dessus — c'est un oubli d'argument.
            # FIX: nnregr(input_dim, hidden_dim)
            model = nnregr(input_dim, hidden_dim)

            trained_m = self.train_net(model, tx, ty, tc)

            trained_m.eval()
            with torch.no_grad():
                # BUG (crash): même erreur que fit_neuralnet1 — .to('cpu') appliqué sur le tuple, pas sur le tenseur.
                # FIX: torch.cat((ypred, trained_m(vx.to(device)).to('cpu')), 0)
                ypred = torch.cat((ypred, trained_m(vx.to(device)).to("cpu")), 0)
                ytrue = torch.cat((ytrue, vy), 0)
                cens = torch.cat((cens, vc), 0)

        with torch.no_grad():
            mask = cens == 1
            # np.sum(abs(ypred[mask] - ytrue[mask]))  # BUG (qualité): résultat calculé mais jamais assigné — code mort.
            return torch.mean(abs(ypred[mask] - ytrue[mask]))

    def extract_models_mae(
        self,
        model_list=[
            "weibul",
            "gengamma",
            "lognorm",
            "neuralnet1layer",
            "neuralnet2layer",
        ],
    ):
        """
        :param model_list: It does not, by default, run the neural nets.
        :return:
        """
        # create empty dataframe pd with as many rows as model_list lenght and two columns: model and mae
        maedf = pd.DataFrame({"model": model_list, "mae": [None] * len(model_list)})

        for mm in model_list:
            # BUG (logique silencieux): double problème ici.
            # 1. Chained indexing pandas : maedf[...]["mae"] = ... ne modifie pas maedf en place (SettingWithCopyWarning silencieux).
            #    L'assignation se fait sur une copie temporaire — toutes les valeurs mae restent None.
            # 2. Le filtre était sur la chaîne littérale "weibul" au lieu de la variable mm
            #    → même avec un fix du chained indexing, seule la ligne weibul aurait été mise à jour.
            # FIX: maedf.loc avec mm comme variable.
            maedf.loc[maedf["model"] == mm, "mae"] = self.modeldict[mm]()

        return maedf
