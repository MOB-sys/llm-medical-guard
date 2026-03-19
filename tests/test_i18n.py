"""Tests for all locales."""

from llm_medical_guard import MedicalGuard, Severity


class TestChineseGuard:
    def test_chinese_banned(self):
        guard = MedicalGuard(locale="zh")
        result = guard.check("这是包治百病的神药！没有副作用！")
        assert not result.passed
        assert result.severity == Severity.DANGER

    def test_chinese_safe(self):
        guard = MedicalGuard(locale="zh")
        result = guard.check(
            "维生素D可能有助于骨骼健康。"
            "仅供参考。"
            "国家药品监督管理局数据。"
        )
        assert result.passed

    def test_chinese_disclaimer(self):
        guard = MedicalGuard(locale="zh")
        result = guard.check("请咨询医生后再使用。")
        disc = next(c for c in result.checks if c.check_name == "disclaimer")
        assert disc.passed


class TestSpanishGuard:
    def test_spanish_banned(self):
        guard = MedicalGuard(locale="es")
        result = guard.check("Esta cura milagrosa es 100% seguro y sin efectos secundarios!")
        assert not result.passed
        assert result.severity == Severity.DANGER

    def test_spanish_safe(self):
        guard = MedicalGuard(locale="es")
        result = guard.check(
            "La vitamina D puede ayudar a la salud ósea. "
            "Consulte a su médico. "
            "Fuente: OMS."
        )
        assert result.passed

    def test_spanish_disclaimer(self):
        guard = MedicalGuard(locale="es")
        result = guard.check("No sustituye el consejo médico profesional.")
        disc = next(c for c in result.checks if c.check_name == "disclaimer")
        assert disc.passed
