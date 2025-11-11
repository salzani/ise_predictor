import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

"""
    Extreme Gradient Boosting model
"""

class Xgboost:
    def __init__(self, X_train, X_test, y_train, y_test, le):
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.le = le
        self.model = None

    def build_xgboost(self):
        dtrain = xgb.DMatrix(self.X_train, label=self.y_train)
        dtest = xgb.DMatrix(self.X_test, label=self.y_test)

        params = {
            'objective': 'reg:squarederror', 
            'max_depth': 6,                   
            'learning_rate': 0.1,                         
            'random_state': 42                
        }

        num_round = 100
        self.model = xgb.train(params, dtrain, num_round)

        y_pred = self.model.predict(dtest)

        mse = mean_squared_error(self.y_test, y_pred)
        r2 = r2_score(self.y_test, y_pred)
        mae = mean_absolute_error(self.y_test, y_pred)
        
        print("XGBoost trained")
        print(f'  MAE: {mae}')
        print(f'  MSE: {mse}')
        print(f'  R²: {r2}')

        return self.model
    
    def predict_xgboost(self, user_input):
        final_df = user_input.drop(columns=['ID', 'EMPRESA', 'INDICE_SUSTENTABILIDADE'])
        final_df['SETOR'] = self.le.transform(final_df['SETOR'])

        duser = xgb.DMatrix(final_df) 
        xgboost_pred = self.model.predict(duser)

        print(f'Predição do Extreme Gradient Boosting para a entrada atual: {xgboost_pred}')
        return xgboost_pred