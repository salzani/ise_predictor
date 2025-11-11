from sklearn.tree import DecisionTreeRegressor, plot_tree
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder

class RegressionTree:
    def __init__(self, random_state=42):
        self.tree_model = DecisionTreeRegressor(random_state=random_state)
        self.is_trained = False
        self.training_columns = None

    def train_tree(self, X_train, y_train, label_encoder, X_test=None, y_test=None):
        self.training_columns = list(X_train.columns)  
        self.tree_model.fit(X_train, y_train)
        self.label_encoder = label_encoder
        self.is_trained = True

        y_pred = self.tree_model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        print("Regression Tree Model trained")
        print(f"  MAE: {mae}")
        print(f"  MSE: {mse}")
        print(f"  R²: {r2}")

    def predict_tree(self, user_input_df):
        final_df = user_input_df.drop(columns=['ID', 'EMPRESA'])
        
        le = self.label_encoder

        final_df['SETOR'] = le.transform(final_df['SETOR']) 

        X = final_df.drop('INDICE_SUSTENTABILIDADE', axis=1)

        train_columns = ['SETOR', 'USO_AGUA', 'AREA', 'AREA_RESERVA', 
                            'CO2_EMIT_DIR', 'CO2_EMIT_INDIR', 'CO2_REC', 
                            'INSUMO_QUIMICO_LEG', 'INSUMO_QUIMICO_ORG', 
                            'BIODIVERSIDADE', 'RESIDUO_REC', 'RESIDUO_COMP', 
                            'RESIDUO_DESC', 'ENERGIA_REN']

        X_input = X[train_columns]
        
        current_predict = self.tree_model.predict(X_input)
        print(f'Predição da Árvore de Regressão para a entrada atual: {current_predict}')
        return current_predict
