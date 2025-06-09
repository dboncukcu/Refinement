import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config import Config
    from loss import LossManager

from .plot_regression_1d import PlotRegression1D
from .plot_regression_correlation_factors import PlotRegressionCorrelationFactors
from .plot_learning_curves import PlotLearningCurves

class PlotterManager:
    def __init__(self, config: "Config", output_path: str, training_id: str):
        self.config = config
        self.output_path = output_path
        self.training_id = training_id
        self.plot_folder = os.path.join(output_path, "plots")
        
        # Create output directory
        os.makedirs(self.plot_folder, exist_ok=True)
        
        # Initialize individual plotters
        self.regression_1d_plotter = PlotRegression1D(config, self.plot_folder, training_id)
        self.correlation_plotter = PlotRegressionCorrelationFactors(config, self.plot_folder, training_id)
        self.learning_curves_plotter = PlotLearningCurves(config, self.plot_folder, training_id)
    
    def plot_all(self, root_file_path: str, loss_manager: "LossManager" = None):
        """Generate all plots"""
        print(f"Generating plots in {self.plot_folder}")
        
        # Plot 1D regression comparisons
        print("Creating 1D regression plots...")
        self.regression_1d_plotter.create_plots(root_file_path)
        
        # Plot correlation factors
        print("Creating correlation factor plots...")
        self.correlation_plotter.create_plots(root_file_path)
        
        # Plot learning curves if loss manager is provided
        if loss_manager is not None:
            print("Creating learning curves...")
            self.learning_curves_plotter.create_plots(loss_manager)
        
        print("All plots generated successfully!")
    
    def plot_regression_1d(self, root_file_path: str):
        """Generate only 1D regression plots"""
        self.regression_1d_plotter.create_plots(root_file_path)
    
    def plot_correlation_factors(self, root_file_path: str):
        """Generate only correlation factor plots"""
        self.correlation_plotter.create_plots(root_file_path)
    
    def plot_learning_curves(self, loss_manager: "LossManager"):
        """Generate only learning curves"""
        self.learning_curves_plotter.create_plots(loss_manager) 