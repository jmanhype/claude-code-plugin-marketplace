"""
GEPA trainer for optimizing the code safety monitor.

Implements prompt optimization using Genetic-Pareto algorithm with
natural language reflection.
"""

import dspy
from pathlib import Path
from typing import Optional, List
import os

from .monitor import CodeSafetyMonitor, MonitorTrainerProgram
from .metrics import comparative_metric, finetune_metric


class GEPATrainer:
    """
    Trainer for optimizing monitor using GEPA (Genetic-Pareto) algorithm.

    GEPA uses natural language reflection to iteratively improve prompts,
    achieving better separation of honest vs attack code distributions.
    """

    def __init__(
        self,
        monitor: CodeSafetyMonitor,
        reflection_model: str = "openai/gpt-5-2025-08-07",
        max_full_evals: int = 2,
        num_threads: int = 8,
        reflection_minibatch_size: int = 3,
        track_stats: bool = True,
        api_key: Optional[str] = None,
    ):
        """
        Initialize GEPA trainer.

        Args:
            monitor: The monitor to optimize
            reflection_model: Model for reflection/optimization
            max_full_evals: Maximum full evaluations
            num_threads: Number of parallel threads
            reflection_minibatch_size: Size of reflection minibatches
            track_stats: Whether to track optimization statistics
            api_key: Optional API key (uses env var if not provided)
        """
        self.monitor = monitor
        self.reflection_model = reflection_model
        self.max_full_evals = max_full_evals
        self.num_threads = num_threads
        self.reflection_minibatch_size = reflection_minibatch_size
        self.track_stats = track_stats

        # Setup reflection LM
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.reflection_lm = dspy.LM(
            reflection_model,
            temperature=1.0,
            max_tokens=32000,
            api_key=api_key,
        )

        # Initialize GEPA optimizer
        self.optimizer = dspy.GEPA(
            max_full_evals=max_full_evals,
            metric=comparative_metric,
            num_threads=num_threads,
            reflection_minibatch_size=reflection_minibatch_size,
            track_stats=track_stats,
            reflection_lm=self.reflection_lm,
        )

    def train(
        self,
        trainset: List[dspy.Example],
        valset: Optional[List[dspy.Example]] = None,
    ) -> MonitorTrainerProgram:
        """
        Train the monitor using GEPA optimization.

        Args:
            trainset: Training examples (attack + honest code pairs)
            valset: Optional validation set

        Returns:
            Optimized MonitorTrainerProgram
        """
        # Wrap monitor in trainer program for comparative training
        trainer_program = MonitorTrainerProgram(self.monitor)

        # Run GEPA optimization
        print(f"Starting GEPA optimization with {len(trainset)} training samples...")
        print(f"Reflection model: {self.reflection_model}")
        print(f"Max full evaluations: {self.max_full_evals}")

        optimized_program = self.optimizer.compile(
            trainer_program,
            trainset=trainset,
            valset=valset or trainset[:50],  # Use subset if no valset
        )

        print("GEPA optimization complete!")
        print("\nOptimized prompt:")
        print("=" * 80)
        print(optimized_program.monitor.predictor.signature.instructions)
        print("=" * 80)

        return optimized_program

    def save_optimized(
        self,
        optimized_program: MonitorTrainerProgram,
        path: Path,
    ) -> None:
        """Save the optimized monitor."""
        optimized_program.monitor.save(path)
        print(f"Optimized monitor saved to: {path}")


class FinetuneTrainer:
    """
    Trainer for fine-tuning the monitor after GEPA optimization.

    Uses Bootstrap fine-tuning to further improve performance by
    updating model weights on correct predictions.
    """

    def __init__(
        self,
        monitor: CodeSafetyMonitor,
    ):
        """
        Initialize fine-tune trainer.

        Args:
            monitor: The monitor to fine-tune (should be GEPA-optimized)
        """
        self.monitor = monitor

        # Initialize Bootstrap fine-tuning optimizer
        self.optimizer = dspy.BootstrapFinetune(
            metric=finetune_metric,
        )

    def train(
        self,
        trainset: List[dspy.Example],
    ) -> MonitorTrainerProgram:
        """
        Fine-tune the monitor using Bootstrap fine-tuning.

        Args:
            trainset: Training examples

        Returns:
            Fine-tuned MonitorTrainerProgram
        """
        # Wrap monitor in trainer program
        trainer_program = MonitorTrainerProgram(self.monitor)

        print(f"Starting Bootstrap fine-tuning with {len(trainset)} samples...")

        # Run fine-tuning
        finetuned_program = self.optimizer.compile(
            trainer_program,
            trainset=trainset,
        )

        print("Fine-tuning complete!")

        return finetuned_program

    def save_finetuned(
        self,
        finetuned_program: MonitorTrainerProgram,
        path: Path,
    ) -> None:
        """Save the fine-tuned monitor."""
        finetuned_program.monitor.save(path)
        print(f"Fine-tuned monitor saved to: {path}")


def train_pipeline(
    trainset: List[dspy.Example],
    valset: Optional[List[dspy.Example]] = None,
    monitor_model: str = "openai/gpt-4.1-nano-2025-04-14",
    reflection_model: str = "openai/gpt-5-2025-08-07",
    output_dir: Path = Path("models"),
    run_finetune: bool = False,
) -> CodeSafetyMonitor:
    """
    Complete training pipeline: GEPA optimization + optional fine-tuning.

    Args:
        trainset: Training examples
        valset: Optional validation set
        monitor_model: Model for the monitor
        reflection_model: Model for GEPA reflection
        output_dir: Directory to save models
        run_finetune: Whether to run fine-tuning after GEPA

    Returns:
        Fully trained monitor
    """
    output_dir.mkdir(exist_ok=True, parents=True)

    # Step 1: Create base monitor
    print("Step 1: Creating base monitor...")
    monitor = CodeSafetyMonitor(model=monitor_model)

    # Step 2: GEPA optimization
    print("\nStep 2: Running GEPA optimization...")
    gepa_trainer = GEPATrainer(monitor, reflection_model=reflection_model)
    gepa_program = gepa_trainer.train(trainset, valset)

    gepa_path = output_dir / "gepa_optimized.json"
    gepa_trainer.save_optimized(gepa_program, gepa_path)

    # Step 3: Optional fine-tuning
    if run_finetune:
        print("\nStep 3: Running Bootstrap fine-tuning...")
        finetune_trainer = FinetuneTrainer(gepa_program.monitor)
        finetuned_program = finetune_trainer.train(trainset)

        finetune_path = output_dir / "gepa_finetuned.json"
        finetune_trainer.save_finetuned(finetuned_program, finetune_path)

        return finetuned_program.monitor
    else:
        print("\nSkipping fine-tuning (set run_finetune=True to enable)")
        return gepa_program.monitor
