"""
JD-Scanner - AI 기반 채용공고 분석 시스템 src 패키지
"""

from .chain import JobSummaryChain, SkillGapChain
from .config_manager import ConfigManager
from .discord_sender import SimpleDiscordSender
from .email_sender import SimpleEmailSender
from .github_analyzer import GitHubAnalyzer, GitHubProfile, Repository
from .lang_prompt import PromptConfig
from .lang_template import JobSummaryTemplate, SkillGapTemplate
from .main_ui import MainWindow
from .settings_ui import SettingsWindow
from .user_manager import UserManager, UserProfile

__all__ = [
    # 체인
    "JobSummaryChain",
    "SkillGapChain",
    # 프롬프트/템플릿
    "PromptConfig",
    "JobSummaryTemplate",
    "SkillGapTemplate",
    # 알림
    "SimpleDiscordSender",
    "SimpleEmailSender",
    # GitHub
    "GitHubAnalyzer",
    "GitHubProfile",
    "Repository",
    # 사용자
    "UserManager",
    "UserProfile",
    # 설정
    "ConfigManager",
    # GUI
    "MainWindow",
    "SettingsWindow",
]
