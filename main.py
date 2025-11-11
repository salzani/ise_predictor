import sys
import pandas as pd
from PyQt6.QtWidgets import QApplication, QMessageBox
from data.data_treatment import DataTreatment 
from models.DEC_TREE import RegressionTree
from models.MLP import NeuralNetwork
from models.XGBoost import Xgboost
from models.gemma_orchestrator import ISEOrchestrator
from app.integrated_ui import IntegratedMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    model_path = 'models/gemma-2b-FT'
    prompts_path = 'prompts/brain_prompt.yaml'
    
    orchestrator = ISEOrchestrator(model_path, prompts_path)

    training_df = pd.read_csv('data/db/datasetEsgTRAIN.csv')
    
    try:
        print("01- Data treatment")
        inst = DataTreatment(training_df.copy())
        X_train_tree, X_test_tree, y_train_tree, y_test_tree, le_tree = inst.tree_treatment()
        X_train_mlp, X_test_mlp, y_train_mlp, y_test_mlp, preprocessor = inst.mlp_treatment()
        X_train_xg, X_test_xg, y_train_xg, y_test_xg, le_processor = inst.xgboost_treatment()
        print("01- Finished\n")

        print("02- Training Regression Tree")
        reg_tree = RegressionTree()
        reg_tree.train_tree(X_train_tree, y_train_tree, le_tree, X_test_tree, y_test_tree)
        print("02- Finished\n")
        
        print("03- Training MLP")
        mlp_nn = NeuralNetwork(X_train_mlp, X_test_mlp, y_train_mlp, y_test_mlp, preprocessor)
        mlp_nn.train_mlp()
        print("03- Finished\n")
        
        print("04- Training XGBoost")
        xg_boost = Xgboost(X_train_xg, X_test_xg, y_train_xg, y_test_xg, le_processor)
        xg_boost.build_xgboost()
        print("04- Finished\n")
        
        print("Initializing Integrated UI")
        main_window = IntegratedMainWindow(reg_tree, mlp_nn, xg_boost, preprocessor, orchestrator)
        main_window.show()
        
        sys.exit(app.exec())
        
    except Exception as e:
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setText("Error")
        error_box.setInformativeText(f"Training error.\n\nDetails: {e}")
        error_box.exec()
        sys.exit(1)