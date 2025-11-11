import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder,  OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

"""
    Dropando as colunas que não serão usadas no treinamento dos modelos
    Splitando o dataset entre treino e teste
    TARGET: INDICE_SUSTENTABILIDADE
    Adicionando encoder na coluna 'SETOR'
"""

class DataTreatment:
    def __init__(self, df):
        self.df = df
        self.preprocessor = None

    def tree_treatment(self):
        final_df = self.df.drop(columns=['ID', 'EMPRESA'])

        le = LabelEncoder()

        final_df['SETOR'] = le.fit_transform(final_df['SETOR']) 

        X = final_df.drop('INDICE_SUSTENTABILIDADE', axis=1)
        y = final_df['INDICE_SUSTENTABILIDADE']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        return X_train, X_test, y_train, y_test, le
    
    def mlp_treatment(self):

        final_df = self.df.drop(columns=['ID', 'EMPRESA'])

        X = final_df.drop('INDICE_SUSTENTABILIDADE', axis=1)
        y = final_df['INDICE_SUSTENTABILIDADE']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        cat_features = ['SETOR']

        num_features = X_train.columns.difference(cat_features) 

        self.preprocessor = ColumnTransformer(transformers=[
            ('num', StandardScaler(), num_features),
            ('cat', OneHotEncoder(sparse_output=False, handle_unknown='ignore'), cat_features)
        ])

        X_train_processed = self.preprocessor.fit_transform(X_train)

        X_test_processed = self.preprocessor.transform(X_test)

        return X_train_processed, X_test_processed, y_train, y_test, self.preprocessor
    
    def xgboost_treatment(self):
        final_df = self.df.drop(columns=['ID', 'EMPRESA'])

        le = LabelEncoder()

        final_df['SETOR'] = le.fit_transform(final_df['SETOR']).astype(int)

        X = final_df.drop('INDICE_SUSTENTABILIDADE', axis=1)
        y = final_df['INDICE_SUSTENTABILIDADE']

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        return X_train, X_test, y_train, y_test, le