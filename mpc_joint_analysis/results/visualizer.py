"""
Results Visualizer Module

Handles visualization of results from MPC computations in a privacy-preserving
manner, including charts, graphs, and statistical summaries.
"""

import logging
import json
import base64
import io
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress matplotlib warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

class VisualizerError(Exception):
    """Custom exception for visualizer errors."""
    pass

class ChartType(Enum):
    """Types of charts that can be generated."""
    LINE = "line"
    BAR = "bar"
    HISTOGRAM = "histogram"
    PIE = "pie"
    SCATTER = "scatter"
    BOX = "box"
    HEATMAP = "heatmap"
    VIOLIN = "violin"
    CORRELATION_MATRIX = "correlation_matrix"
    DISTRIBUTION = "distribution"
    TIME_SERIES = "time_series"
    COMPARISON = "comparison"

class OutputFormat(Enum):
    """Output formats for visualizations."""
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    HTML = "html"
    JSON = "json"

@dataclass
class VisualizationConfig:
    """Configuration for visualization generation."""
    title: str
    chart_type: ChartType
    data_source: str
    privacy_level: str = "medium"
    width: int = 800
    height: int = 600
    color_scheme: str = "default"
    show_legend: bool = True
    show_grid: bool = True
    annotations: List[str] = None
    
    def __post_init__(self):
        if self.annotations is None:
            self.annotations = []

@dataclass
class VisualizationResult:
    """Result of a visualization operation."""
    chart_data: bytes
    format: OutputFormat
    metadata: Dict[str, Any]
    privacy_applied: bool
    chart_type: ChartType
    timestamp: float
    
    def to_base64(self) -> str:
        """Convert chart data to base64 string."""
        return base64.b64encode(self.chart_data).decode('utf-8')

class PrivacyAwareVisualizer:
    """Handles privacy-aware visualization of MPC results."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.privacy_settings = config.get('privacy_settings', {})
        self.default_style = config.get('default_style', 'seaborn')
        self.color_schemes = self._initialize_color_schemes()
        
        # Set up matplotlib style
        plt.style.use(self.default_style)
        
        logger.info("Privacy-aware visualizer initialized")
    
    def _initialize_color_schemes(self) -> Dict[str, List[str]]:
        """Initialize color schemes for visualizations."""
        return {
            'default': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            'professional': ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#592E83'],
            'pastel': ['#FFB3BA', '#FFDFBA', '#FFFFBA', '#BAFFC9', '#BAE1FF'],
            'monochrome': ['#2C3E50', '#34495E', '#7F8C8D', '#95A5A6', '#BDC3C7'],
            'high_contrast': ['#000000', '#FF0000', '#00FF00', '#0000FF', '#FFFF00']
        }
    
    def create_visualization(self, data: Any, config: VisualizationConfig,
                           output_format: OutputFormat = OutputFormat.PNG) -> VisualizationResult:
        """Create a privacy-aware visualization."""
        try:
            # Apply privacy filters to data
            filtered_data = self._apply_privacy_filters(data, config)
            
            # Generate chart based on type
            chart_generator = self._get_chart_generator(config.chart_type)
            if not chart_generator:
                raise VisualizerError(f"Unsupported chart type: {config.chart_type}")
            
            # Create the visualization
            fig, ax = chart_generator(filtered_data, config)
            
            # Apply styling
            self._apply_styling(fig, ax, config)
            
            # Convert to output format
            chart_data = self._convert_to_format(fig, output_format)
            
            # Close the figure to free memory
            plt.close(fig)
            
            # Create result
            result = VisualizationResult(
                chart_data=chart_data,
                format=output_format,
                metadata={
                    'title': config.title,
                    'chart_type': config.chart_type.value,
                    'privacy_level': config.privacy_level,
                    'data_points': self._count_data_points(filtered_data),
                    'width': config.width,
                    'height': config.height
                },
                privacy_applied=True,
                chart_type=config.chart_type,
                timestamp=time.time()
            )
            
            logger.info(f"Created {config.chart_type.value} visualization")
            return result
            
        except Exception as e:
            logger.error(f"Error creating visualization: {e}")
            raise VisualizerError(f"Failed to create visualization: {e}")
    
    def _apply_privacy_filters(self, data: Any, config: VisualizationConfig) -> Any:
        """Apply privacy filters to data before visualization."""
        privacy_level = config.privacy_level
        
        if privacy_level == "low":
            # Minimal privacy filtering
            return self._apply_minimal_privacy(data)
        elif privacy_level == "medium":
            # Standard privacy filtering
            return self._apply_standard_privacy(data)
        elif privacy_level == "high":
            # Strong privacy filtering
            return self._apply_strong_privacy(data)
        else:
            return data
    
    def _apply_minimal_privacy(self, data: Any) -> Any:
        """Apply minimal privacy filtering."""
        # Round numeric values to reduce precision
        if isinstance(data, (int, float)):
            return round(data, 2)
        elif isinstance(data, np.ndarray):
            return np.round(data, 2)
        elif isinstance(data, list):
            return [round(x, 2) if isinstance(x, (int, float)) else x for x in data]
        elif isinstance(data, dict):
            return {k: round(v, 2) if isinstance(v, (int, float)) else v 
                   for k, v in data.items()}
        return data
    
    def _apply_standard_privacy(self, data: Any) -> Any:
        """Apply standard privacy filtering."""
        # Add small amount of noise and round
        if isinstance(data, (int, float)):
            noise = np.random.normal(0, abs(data) * 0.01)
            return round(data + noise, 1)
        elif isinstance(data, np.ndarray):
            noise = np.random.normal(0, np.abs(data) * 0.01)
            return np.round(data + noise, 1)
        elif isinstance(data, list):
            return [self._apply_standard_privacy(x) for x in data]
        elif isinstance(data, dict):
            return {k: self._apply_standard_privacy(v) for k, v in data.items()}
        return data
    
    def _apply_strong_privacy(self, data: Any) -> Any:
        """Apply strong privacy filtering."""
        # Add more noise and suppress small values
        if isinstance(data, (int, float)):
            if abs(data) < 5:  # Suppress small values
                return 0
            noise = np.random.normal(0, abs(data) * 0.05)
            return round(data + noise, 0)
        elif isinstance(data, np.ndarray):
            # Suppress small values
            data_copy = data.copy()
            data_copy[np.abs(data_copy) < 5] = 0
            noise = np.random.normal(0, np.abs(data_copy) * 0.05)
            return np.round(data_copy + noise, 0)
        elif isinstance(data, list):
            return [self._apply_strong_privacy(x) for x in data]
        elif isinstance(data, dict):
            return {k: self._apply_strong_privacy(v) for k, v in data.items()}
        return data
    
    def _get_chart_generator(self, chart_type: ChartType) -> Optional[callable]:
        """Get the appropriate chart generator function."""
        generators = {
            ChartType.LINE: self._create_line_chart,
            ChartType.BAR: self._create_bar_chart,
            ChartType.HISTOGRAM: self._create_histogram,
            ChartType.PIE: self._create_pie_chart,
            ChartType.SCATTER: self._create_scatter_plot,
            ChartType.BOX: self._create_box_plot,
            ChartType.HEATMAP: self._create_heatmap,
            ChartType.VIOLIN: self._create_violin_plot,
            ChartType.CORRELATION_MATRIX: self._create_correlation_matrix,
            ChartType.DISTRIBUTION: self._create_distribution_plot,
            ChartType.TIME_SERIES: self._create_time_series,
            ChartType.COMPARISON: self._create_comparison_chart
        }
        return generators.get(chart_type)
    
    def _create_line_chart(self, data: Any, config: VisualizationConfig) -> Tuple[plt.Figure, plt.Axes]:
        """Create a line chart."""
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        if isinstance(data, dict):
            for label, values in data.items():
                ax.plot(values, label=label, linewidth=2)
        elif isinstance(data, list):
            ax.plot(data, linewidth=2)
        else:
            ax.plot(data, linewidth=2)
        
        ax.set_title(config.title, fontsize=14, fontweight='bold')
        return fig, ax
    
    def _create_bar_chart(self, data: Any, config: VisualizationConfig) -> Tuple[plt.Figure, plt.Axes]:
        """Create a bar chart."""
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        if isinstance(data, dict):
            categories = list(data.keys())
            values = list(data.values())
            bars = ax.bar(categories, values, color=self.color_schemes[config.color_scheme])
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{value:.1f}', ha='center', va='bottom')
        
        ax.set_title(config.title, fontsize=14, fontweight='bold')
        return fig, ax
    
    def _create_histogram(self, data: Any, config: VisualizationConfig) -> Tuple[plt.Figure, plt.Axes]:
        """Create a histogram."""
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        if isinstance(data, (list, np.ndarray)):
            ax.hist(data, bins=30, alpha=0.7, color=self.color_schemes[config.color_scheme][0])
        
        ax.set_title(config.title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Value')
        ax.set_ylabel('Frequency')
        return fig, ax
    
    def _create_pie_chart(self, data: Any, config: VisualizationConfig) -> Tuple[plt.Figure, plt.Axes]:
        """Create a pie chart."""
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        if isinstance(data, dict):
            labels = list(data.keys())
            values = list(data.values())
            wedges, texts, autotexts = ax.pie(values, labels=labels, autopct='%1.1f%%',
                                            colors=self.color_schemes[config.color_scheme])
            
            # Enhance text appearance
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
        
        ax.set_title(config.title, fontsize=14, fontweight='bold')
        return fig, ax
    
    def _create_scatter_plot(self, data: Any, config: VisualizationConfig) -> Tuple[plt.Figure, plt.Axes]:
        """Create a scatter plot."""
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        if isinstance(data, dict) and 'x' in data and 'y' in data:
            ax.scatter(data['x'], data['y'], alpha=0.7, 
                      color=self.color_schemes[config.color_scheme][0])
        
        ax.set_title(config.title, fontsize=14, fontweight='bold')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        return fig, ax
    
    def _create_box_plot(self, data: Any, config: VisualizationConfig) -> Tuple[plt.Figure, plt.Axes]:
        """Create a box plot."""
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        if isinstance(data, dict):
            labels = list(data.keys())
            values = list(data.values())
            box_plot = ax.boxplot(values, labels=labels, patch_artist=True)
            
            # Color the boxes
            colors = self.color_schemes[config.color_scheme]
            for patch, color in zip(box_plot['boxes'], colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
        
        ax.set_title(config.title, fontsize=14, fontweight='bold')
        return fig, ax
    
    def _create_heatmap(self, data: Any, config: VisualizationConfig) -> Tuple[plt.Figure, plt.Axes]:
        """Create a heatmap."""
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        if isinstance(data, np.ndarray):
            im = ax.imshow(data, cmap='viridis', aspect='auto')
            plt.colorbar(im, ax=ax)
        elif isinstance(data, pd.DataFrame):
            sns.heatmap(data, ax=ax, cmap='viridis', annot=True, fmt='.2f')
        
        ax.set_title(config.title, fontsize=14, fontweight='bold')
        return fig, ax
    
    def _create_violin_plot(self, data: Any, config: VisualizationConfig) -> Tuple[plt.Figure, plt.Axes]:
        """Create a violin plot."""
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        if isinstance(data, dict):
            labels = list(data.keys())
            values = list(data.values())
            violin_parts = ax.violinplot(values, positions=range(len(labels)))
            
            # Color the violin plots
            colors = self.color_schemes[config.color_scheme]
            for pc, color in zip(violin_parts['bodies'], colors):
                pc.set_facecolor(color)
                pc.set_alpha(0.7)
            
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels)
        
        ax.set_title(config.title, fontsize=14, fontweight='bold')
        return fig, ax
    
    def _create_correlation_matrix(self, data: Any, config: VisualizationConfig) -> Tuple[plt.Figure, plt.Axes]:
        """Create a correlation matrix."""
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        if isinstance(data, pd.DataFrame):
            corr_matrix = data.corr()
            sns.heatmap(corr_matrix, ax=ax, annot=True, cmap='coolwarm', 
                       center=0, fmt='.2f', square=True)
        
        ax.set_title(config.title, fontsize=14, fontweight='bold')
        return fig, ax
    
    def _create_distribution_plot(self, data: Any, config: VisualizationConfig) -> Tuple[plt.Figure, plt.Axes]:
        """Create a distribution plot."""
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        if isinstance(data, (list, np.ndarray)):
            ax.hist(data, bins=30, alpha=0.7, density=True, 
                   color=self.color_schemes[config.color_scheme][0])
            
            # Add kernel density estimation
            from scipy import stats
            kde = stats.gaussian_kde(data)
            x_range = np.linspace(min(data), max(data), 100)
            ax.plot(x_range, kde(x_range), 'r-', linewidth=2)
        
        ax.set_title(config.title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Value')
        ax.set_ylabel('Density')
        return fig, ax
    
    def _create_time_series(self, data: Any, config: VisualizationConfig) -> Tuple[plt.Figure, plt.Axes]:
        """Create a time series plot."""
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        if isinstance(data, dict) and 'timestamps' in data and 'values' in data:
            ax.plot(data['timestamps'], data['values'], 
                   color=self.color_schemes[config.color_scheme][0], linewidth=2)
        
        ax.set_title(config.title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Time')
        ax.set_ylabel('Value')
        return fig, ax
    
    def _create_comparison_chart(self, data: Any, config: VisualizationConfig) -> Tuple[plt.Figure, plt.Axes]:
        """Create a comparison chart."""
        fig, ax = plt.subplots(figsize=(config.width/100, config.height/100))
        
        if isinstance(data, dict):
            categories = list(data.keys())
            values = list(data.values())
            
            # Create grouped bar chart if values are lists
            if all(isinstance(v, (list, np.ndarray)) for v in values):
                x = np.arange(len(categories))
                width = 0.35
                
                for i, (category, value_list) in enumerate(data.items()):
                    ax.bar(x + i*width, value_list, width, label=category,
                          color=self.color_schemes[config.color_scheme][i])
                
                ax.set_xticks(x + width/2)
                ax.set_xticklabels(categories)
            else:
                # Simple bar chart
                ax.bar(categories, values, color=self.color_schemes[config.color_scheme])
        
        ax.set_title(config.title, fontsize=14, fontweight='bold')
        return fig, ax
    
    def _apply_styling(self, fig: plt.Figure, ax: plt.Axes, config: VisualizationConfig):
        """Apply styling to the visualization."""
        # Set grid
        if config.show_grid:
            ax.grid(True, alpha=0.3)
        
        # Set legend
        if config.show_legend and ax.get_legend_handles_labels()[0]:
            ax.legend(loc='best')
        
        # Add annotations
        for annotation in config.annotations:
            ax.annotate(annotation, xy=(0.5, 0.95), xycoords='axes fraction',
                       ha='center', va='top', fontsize=10)
        
        # Adjust layout
        fig.tight_layout()
    
    def _convert_to_format(self, fig: plt.Figure, output_format: OutputFormat) -> bytes:
        """Convert figure to specified output format."""
        buffer = io.BytesIO()
        
        if output_format == OutputFormat.PNG:
            fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        elif output_format == OutputFormat.SVG:
            fig.savefig(buffer, format='svg', bbox_inches='tight')
        elif output_format == OutputFormat.PDF:
            fig.savefig(buffer, format='pdf', bbox_inches='tight')
        else:
            raise VisualizerError(f"Unsupported output format: {output_format}")
        
        buffer.seek(0)
        return buffer.read()
    
    def _count_data_points(self, data: Any) -> int:
        """Count the number of data points."""
        if isinstance(data, (list, np.ndarray)):
            return len(data)
        elif isinstance(data, dict):
            return sum(len(v) if isinstance(v, (list, np.ndarray)) else 1 
                      for v in data.values())
        elif isinstance(data, pd.DataFrame):
            return len(data)
        else:
            return 1
    
    def create_dashboard(self, visualizations: List[VisualizationResult],
                        title: str = "MPC Analysis Dashboard") -> bytes:
        """Create a dashboard with multiple visualizations."""
        try:
            # Create subplot grid
            n_charts = len(visualizations)
            cols = min(3, n_charts)
            rows = (n_charts + cols - 1) // cols
            
            fig, axes = plt.subplots(rows, cols, figsize=(15, 5*rows))
            if rows == 1 and cols == 1:
                axes = [axes]
            elif rows == 1 or cols == 1:
                axes = axes.flatten()
            else:
                axes = axes.flatten()
            
            # Add each visualization to the dashboard
            for i, vis_result in enumerate(visualizations):
                if i < len(axes):
                    # Convert bytes back to image and display
                    # Note: This is a simplified approach
                    # In practice, you'd need to recreate the chart
                    axes[i].text(0.5, 0.5, f"Chart {i+1}\n{vis_result.metadata.get('title', '')}", 
                               ha='center', va='center', transform=axes[i].transAxes)
                    axes[i].set_title(vis_result.metadata.get('title', f'Chart {i+1}'))
            
            # Hide unused subplots
            for i in range(n_charts, len(axes)):
                axes[i].set_visible(False)
            
            # Add main title
            fig.suptitle(title, fontsize=16, fontweight='bold')
            fig.tight_layout()
            
            # Convert to bytes
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            
            plt.close(fig)
            return buffer.read()
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            raise VisualizerError(f"Failed to create dashboard: {e}")
    
    def generate_statistical_summary(self, data: Any) -> Dict[str, Any]:
        """Generate a statistical summary of the data."""
        summary = {}
        
        if isinstance(data, (list, np.ndarray)):
            data_array = np.array(data)
            summary = {
                'count': len(data_array),
                'mean': float(np.mean(data_array)),
                'std': float(np.std(data_array)),
                'min': float(np.min(data_array)),
                'max': float(np.max(data_array)),
                'median': float(np.median(data_array)),
                'q25': float(np.percentile(data_array, 25)),
                'q75': float(np.percentile(data_array, 75))
            }
        elif isinstance(data, pd.DataFrame):
            summary = data.describe().to_dict()
        elif isinstance(data, dict):
            summary = {k: self.generate_statistical_summary(v) for k, v in data.items()}
        
        return summary
    
    def export_visualization_data(self, result: VisualizationResult, 
                                 include_raw_data: bool = False) -> Dict[str, Any]:
        """Export visualization data in JSON format."""
        export_data = {
            'metadata': result.metadata,
            'chart_type': result.chart_type.value,
            'format': result.format.value,
            'privacy_applied': result.privacy_applied,
            'timestamp': result.timestamp,
            'chart_base64': result.to_base64()
        }
        
        if include_raw_data:
            export_data['raw_data'] = result.chart_data.decode('utf-8', errors='ignore')
        
        return export_data
    
    def get_visualization_statistics(self) -> Dict[str, Any]:
        """Get statistics about visualizations created."""
        # This would typically track visualizations created
        # For now, return basic information
        return {
            'supported_chart_types': [ct.value for ct in ChartType],
            'supported_formats': [of.value for of in OutputFormat],
            'available_color_schemes': list(self.color_schemes.keys()),
            'privacy_levels': ['low', 'medium', 'high']
        }