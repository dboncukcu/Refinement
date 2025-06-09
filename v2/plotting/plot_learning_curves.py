import matplotlib.pyplot as plt
import os
from typing import TYPE_CHECKING, Dict, List, Tuple

if TYPE_CHECKING:
    from config import Config
    from loss import LossManager

class PlotLearningCurves:
    def __init__(self, config: "Config", output_folder: str, training_id: str):
        self.config = config
        self.output_folder = output_folder
        self.training_id = training_id
        
    def create_plots(self, loss_manager: "LossManager"):
        loss_names = list(loss_manager.loss_funcs.keys())
        primary_loss = loss_manager.primary_loss
        
        if not loss_names:
            print("No loss functions found")
            return
        
        # Veriyi bir kere oku ve hazırla
        processed_data = self._preprocess_data(loss_manager, loss_names)
        
        for loss_name in loss_names:
            self._plot_loss(loss_name, processed_data[loss_name])
        
        if primary_loss:
            self._plot_primary_loss(primary_loss, processed_data[primary_loss])
        
        self._plot_all_losses(loss_manager, loss_names, processed_data)
    
    def _preprocess_data(self, loss_manager: "LossManager", loss_names: List[str]) -> Dict[str, Dict[str, Tuple[List[int], List[float]]]]:
        """Tüm loss verilerini bir kere işle ve hazırla"""
        processed_data = {}
        
        for loss_name in loss_names:
            train_epochs = sorted(set(entry.epoch for entry in loss_manager.loss_log.train[loss_name]))
            val_epochs = sorted(set(entry.epoch for entry in loss_manager.loss_log.validation[loss_name]))
            
            # Training averages
            train_avgs = []
            valid_train_epochs = []
            for epoch in train_epochs:
                try:
                    avg = loss_manager.get_epoch_average(loss_name, epoch, is_val=False)
                    train_avgs.append(avg)
                    valid_train_epochs.append(epoch)
                except ValueError:
                    continue
            
            # Validation averages
            val_avgs = []
            valid_val_epochs = []
            for epoch in val_epochs:
                try:
                    avg = loss_manager.get_epoch_average(loss_name, epoch, is_val=True)
                    val_avgs.append(avg)
                    valid_val_epochs.append(epoch)
                except ValueError:
                    continue
            
            processed_data[loss_name] = {
                'train': (valid_train_epochs, train_avgs),
                'validation': (valid_val_epochs, val_avgs)
            }
        
        return processed_data
    
    def _plot_loss(self, loss_name: str, data: Dict[str, Tuple[List[int], List[float]]]):
        train_epochs, train_avgs = data['train']
        val_epochs, val_avgs = data['validation']
        
        plt.figure(figsize=(10, 6))
        
        if train_epochs:
            plt.plot(train_epochs, train_avgs, 'b-o', label='Training', linewidth=2, markersize=4)
        
        if val_epochs:
            plt.plot(val_epochs, val_avgs, 'r-s', label='Validation', linewidth=2, markersize=4)
        
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title(f'Learning Curve - {loss_name}')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        filename = os.path.join(self.output_folder, f'learning_curve_{loss_name}.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved: {filename}")
    
    def _plot_primary_loss(self, primary_loss: str, data: Dict[str, Tuple[List[int], List[float]]]):
        train_epochs, train_avgs = data['train']
        val_epochs, val_avgs = data['validation']
        
        plt.figure(figsize=(12, 8))
        
        if train_epochs:
            plt.plot(train_epochs, train_avgs, 'b-o', label='Training', linewidth=3, markersize=6)
        
        if val_epochs:
            plt.plot(val_epochs, val_avgs, 'r-s', label='Validation', linewidth=3, markersize=6)
        
        plt.xlabel('Epoch', fontsize=12)
        plt.ylabel('Loss', fontsize=12)
        plt.title(f'Primary Loss - {primary_loss}', fontsize=14, fontweight='bold')
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)
        
        filename = os.path.join(self.output_folder, f'primary_loss_{primary_loss}.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved: {filename}")
    
    def _plot_all_losses(self, loss_manager: "LossManager", loss_names: list, processed_data: Dict[str, Dict[str, Tuple[List[int], List[float]]]]):
        n_losses = len(loss_names)
        if n_losses == 0:
            return
        
        cols = min(3, n_losses)
        rows = (n_losses + cols - 1) // cols
        
        fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 4*rows))
        
        if n_losses == 1:
            axes = [axes]
        elif rows == 1:
            axes = [axes] if cols == 1 else axes
        else:
            axes = axes.flatten()
        
        for i, loss_name in enumerate(loss_names):
            ax = axes[i] if n_losses > 1 else axes[0]
            
            train_epochs, train_avgs = processed_data[loss_name]['train']
            val_epochs, val_avgs = processed_data[loss_name]['validation']
            
            if train_epochs:
                ax.plot(train_epochs, train_avgs, 'b-', label='Train', linewidth=2)
            if val_epochs:
                ax.plot(val_epochs, val_avgs, 'r-', label='Val', linewidth=2)
            
            title = f'{loss_name}*' if loss_name == loss_manager.primary_loss else loss_name
            ax.set_title(title, fontweight='bold' if loss_name == loss_manager.primary_loss else 'normal')
            ax.set_xlabel('Epoch')
            ax.set_ylabel('Loss')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        for i in range(n_losses, len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        
        filename = os.path.join(self.output_folder, 'all_learning_curves.png')
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved: {filename}") 