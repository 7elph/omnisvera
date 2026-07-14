from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from omnisvera_model.training import (  # noqa: E402
    backward_preflight,
    configure_gradient_checkpointing,
    trainable_parameter_report,
)


class FakeParameter:
    def __init__(self, count: int, requires_grad: bool):
        self.count = count
        self.requires_grad = requires_grad
        self.grad = None
        self.device = None

    def numel(self) -> int:
        return self.count


class FakeLoss:
    requires_grad = True
    grad_fn = object()

    def __init__(self, parameter: FakeParameter):
        self.parameter = parameter

    def backward(self) -> None:
        self.parameter.grad = object()

    def detach(self):
        return self

    def float(self):
        return self

    def item(self) -> float:
        return 1.25


class FakeOutputs:
    def __init__(self, loss: FakeLoss):
        self.loss = loss


class FakeConfig:
    use_cache = True


class FakeModel:
    def __init__(self):
        self.base = FakeParameter(1000, False)
        self.lora = FakeParameter(20, True)
        self.config = FakeConfig()
        self.input_grads_enabled = False
        self.checkpointing_kwargs = None
        self.training = False

    def named_parameters(self):
        return [("base_model.weight", self.base), ("base_model.q_proj.lora_A.default.weight", self.lora)]

    def enable_input_require_grads(self):
        self.input_grads_enabled = True

    def gradient_checkpointing_enable(self, gradient_checkpointing_kwargs=None):
        self.checkpointing_kwargs = gradient_checkpointing_kwargs

    def train(self):
        self.training = True

    def zero_grad(self, set_to_none=True):
        self.base.grad = None
        self.lora.grad = None

    def __call__(self, **batch):
        return FakeOutputs(FakeLoss(self.lora))


class BrokenLossModel(FakeModel):
    def __call__(self, **batch):
        class BrokenLoss(FakeLoss):
            requires_grad = False
            grad_fn = None

        return FakeOutputs(BrokenLoss(self.lora))


class LoraGradientPreflightTests(unittest.TestCase):
    def test_lora_has_trainable_parameters_and_base_is_frozen(self):
        report = trainable_parameter_report(FakeModel())
        self.assertEqual(20, report["trainable_parameters"])
        self.assertEqual(1, report["trainable_lora_tensors"])
        self.assertTrue(report["base_parameters_frozen"])

    def test_zero_trainable_parameters_is_rejected(self):
        model = FakeModel()
        model.lora.requires_grad = False
        with self.assertRaisesRegex(RuntimeError, "nenhum parâmetro treinável"):
            trainable_parameter_report(model)

    def test_checkpointing_enables_inputs_and_disables_cache(self):
        model = FakeModel()
        report = configure_gradient_checkpointing(model, True)
        self.assertTrue(model.input_grads_enabled)
        self.assertFalse(model.config.use_cache)
        self.assertEqual({"use_reentrant": False}, model.checkpointing_kwargs)
        self.assertTrue(report["input_require_grads_enabled"])
        self.assertFalse(report["use_reentrant"])

    def test_checkpointing_disabled_keeps_original_state(self):
        model = FakeModel()
        report = configure_gradient_checkpointing(model, False)
        self.assertTrue(model.config.use_cache)
        self.assertFalse(model.input_grads_enabled)
        self.assertIsNone(model.checkpointing_kwargs)
        self.assertFalse(report["gradient_checkpointing"])

    def test_forward_loss_is_trainable_and_backward_reaches_lora(self):
        model = FakeModel()
        configure_gradient_checkpointing(model, True)
        report = backward_preflight(model, {"input_ids": object(), "labels": object()})
        self.assertTrue(report["passed"])
        self.assertTrue(report["loss_requires_grad"])
        self.assertTrue(report["loss_has_grad_fn"])
        self.assertEqual(1, report["lora_tensors_with_gradient"])
        self.assertFalse(report["optimizer_step_performed"])
        self.assertIsNone(model.lora.grad, "preflight deve limpar gradientes")

    def test_loss_without_graph_is_rejected(self):
        model = BrokenLossModel()
        with self.assertRaisesRegex(RuntimeError, "loss.requires_grad=False"):
            backward_preflight(model, {"input_ids": object()})


if __name__ == "__main__":
    unittest.main()
