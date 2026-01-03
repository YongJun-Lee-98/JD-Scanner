#!/usr/bin/env python3
"""
JD-Scanner - AI 기반 채용공고 분석 및 면접 준비 시스템
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

from src.chain import JobSummaryChain, SkillGapChain
from src.discord_sender import SimpleDiscordSender
from src.email_sender import SimpleEmailSender
from src.github_analyzer import GitHubAnalyzer
from src.user_manager import UserManager, UserProfile


class JobPostingSummarizer:
    """채용공고 요약 및 분석 클래스"""

    def __init__(self, model_name: str = "gpt-oss:20b"):
        """채용공고 요약기 초기화"""
        self.chain = JobSummaryChain(model_name)
        self.skill_gap_chain = SkillGapChain(model_name)
        self.github_analyzer = GitHubAnalyzer()
        self.user_manager = UserManager()

    def extract_content_from_url(self, url: str) -> str:
        """URL에서 채용공고 내용 추출"""
        try:
            # User-Agent 헤더 추가
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            for script in soup(["script", "style"]):
                script.decompose()

            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = " ".join(chunk for chunk in chunks if chunk)

            if not content.strip():
                raise ValueError("추출된 내용이 비어있습니다.")

            return content

        except requests.exceptions.RequestException as e:
            raise Exception(f"URL 요청 실패: {e}")
        except Exception as e:
            raise Exception(f"내용 추출 실패: {e}")

    def summarize_job_posting(self, content: str, verbose: bool = False) -> str:
        """채용공고 내용 요약 (토큰 제한 자동 처리)"""
        try:
            result = self.chain.run_summary(content, verbose=verbose)
            return result
        except Exception as e:
            raise Exception(f"요약 처리 실패: {e}")

    def save_summary(self, content: str, filename: Optional[str] = None) -> str:
        """결과를 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"job_posting_{timestamp}.md"

        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        file_path = output_dir / filename

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return str(file_path)
        except Exception as e:
            raise Exception(f"파일 저장 실패: {e}")


def main():
    """메인 함수 - 새로운 사용자 플로우"""
    print("=" * 60)
    print("  JD-Scanner - AI 기반 채용공고 분석 및 면접 준비 시스템")
    print("=" * 60)

    try:
        # 초기화
        summarizer = JobPostingSummarizer()

        # Step 1: 사용자 정보 수집
        print("\n[Step 1/6] 사용자 정보 입력")
        user = summarizer.user_manager.collect_user_info()
        print(f"\n환영합니다, {user.email}!")

        # Step 2: 채용공고 URL 입력
        print("\n[Step 2/6] 채용공고 입력")
        print("-" * 40)
        url = input("채용공고 URL을 입력하세요: ").strip()

        if not url or not (url.startswith("http://") or url.startswith("https://")):
            print("올바른 URL 형식이 아닙니다.")
            sys.exit(1)

        # Step 3: 채용공고 분석
        print("\n[Step 3/6] 채용공고 분석")
        print("-" * 40)
        print("내용 추출 중...")
        content = summarizer.extract_content_from_url(url)
        print(f"추출 완료 ({len(content)} 글자)")

        print("AI 요약 처리 중... (시간이 조금 걸릴 수 있습니다)")
        summary = summarizer.summarize_job_posting(content, verbose=True)
        summary_with_link = f"{summary}\n\n[원본 채용공고]({url})"

        # 요약 저장
        saved_path = summarizer.save_summary(summary_with_link)
        print(f"요약 저장 완료: {saved_path}")

        # 결과 변수 초기화
        skill_gap_report = None
        interview_questions_ko = None
        interview_questions_en = None
        full_report = summary_with_link

        # Step 4-5: GitHub 분석 (선택적)
        if user.github_url:
            print("\n[Step 4/6] GitHub 프로필 분석")
            print("-" * 40)
            github_profile = summarizer.github_analyzer.analyze_profile(user.github_url)

            if github_profile:
                # 요구사항 추출
                print("채용 요구사항 추출 중...")
                requirements = summarizer.skill_gap_chain.extract_requirements(summary)

                # 스킬 갭 분석
                print("\n[Step 5/6] 스킬 갭 분석")
                print("-" * 40)
                profile_summary = github_profile.to_summary_dict()
                skill_gap_report = summarizer.skill_gap_chain.analyze_skill_gap(
                    requirements, profile_summary
                )
                print("스킬 갭 분석 완료")

                # 면접 질문 생성 (한국어 + 영어)
                print("\n[Step 6/6] 면접 질문 생성")
                print("-" * 40)
                job_title = requirements.get("job_title", "Software Developer")
                candidate_techs = github_profile.get_all_languages()

                print("한국어 질문 생성 중...")
                interview_questions_ko = (
                    summarizer.skill_gap_chain.generate_interview_questions(
                        skill_gap_report, job_title, candidate_techs, "ko"
                    )
                )

                print("영어 질문 생성 중...")
                interview_questions_en = (
                    summarizer.skill_gap_chain.generate_interview_questions(
                        skill_gap_report, job_title, candidate_techs, "en"
                    )
                )
                print("면접 질문 생성 완료")

                # 전체 리포트 생성
                full_report = f"""# 채용공고 분석 리포트

## 채용공고 요약
{summary_with_link}

---

## 스킬 갭 분석
{skill_gap_report}

---

## 면접 준비 질문 (한국어)
{interview_questions_ko}

---

## Interview Preparation Questions (English)
{interview_questions_en}
"""
                # 전체 리포트 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_path = summarizer.save_summary(
                    full_report, f"full_analysis_{timestamp}.md"
                )
                print(f"전체 분석 리포트 저장: {report_path}")
            else:
                print("GitHub 프로필 분석 실패. 기본 요약만 제공합니다.")
        else:
            print("\n[Step 4-6] GitHub 분석 건너뜀 (프로필 미제공)")

        # 알림 발송
        print("\n" + "=" * 60)
        print("알림 발송 중...")

        # Discord 알림
        try:
            discord_sender = SimpleDiscordSender(summary_with_link)
            discord_sender.run()
        except Exception as e:
            print(f"Discord 발송 실패: {e}")

        # 이메일 알림
        email_sender = SimpleEmailSender(
            message=full_report,
            recipient_email=user.email,
            subject=f"JD-Scanner 분석 결과: {url[:50]}...",
        )
        email_sender.run()

        # 분석 횟수 업데이트
        summarizer.user_manager.increment_analysis_count(user)

        # 결과 출력
        print("\n" + "=" * 60)
        print("분석 완료!")
        print("=" * 60)
        print("\n[채용공고 요약]")
        print("-" * 40)
        print(summary_with_link)

        if skill_gap_report:
            print("\n[스킬 갭 분석]")
            print("-" * 40)
            print(skill_gap_report)

        if interview_questions_ko:
            print("\n[면접 질문 - 한국어]")
            print("-" * 40)
            print(interview_questions_ko)

        if interview_questions_en:
            print("\n[Interview Questions - English]")
            print("-" * 40)
            print(interview_questions_en)

        print("\n" + "=" * 60)
        print(f"이메일 발송 대상: {user.email}")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
