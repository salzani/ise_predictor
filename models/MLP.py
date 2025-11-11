from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


class NeuralNetwork():
    def __init__(self, X_train, X_test, y_train, y_test, preprocessor):
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.mlp = None
        self.preprocessor = preprocessor

    def train_mlp(self):
        self.mlp = MLPRegressor(
            hidden_layer_sizes=(250, 250), 
            activation='relu',
            solver='adam',
            max_iter=1000,
            random_state=42
        )

        self.mlp.fit(self.X_train, self.y_train)

        y_pred = self.mlp.predict(self.X_test)

        mse = mean_squared_error(self.y_test, y_pred)
        mae = mean_absolute_error(self.y_test, y_pred)
        r2 = r2_score(self.y_test, y_pred)
        
        print("Multi-layer Perceptron Model trained")
        print(f'  MAE: {mae}')
        print(f'  MSE: {mse}')
        print(f'  R²: {r2}')
    
    def predict_mlp(self, user_input_df, preprocessor):
        final_df = user_input_df.drop(columns=['ID', 'EMPRESA'])
        
        fit_final_df = preprocessor.transform(final_df)
        
        final_pred = self.mlp.predict(fit_final_df)
        print(f'Predição da Rede Neural para a entrada atual: {final_pred}')
        return final_pred