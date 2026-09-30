# SEO Delivery Guard

**Google Search의 공식 경계에 맞춘 AI 코딩 에이전트용 SEO 개발·릴리스 거버넌스 Skill입니다.**

[![Codex Skill](https://img.shields.io/badge/Codex-Skill-111827?logo=openai&logoColor=white)](../SKILL.md)
[![Version 0.1.0](https://img.shields.io/badge/version-0.1.0-2563eb)](../CHANGELOG.md)
[![MIT License](https://img.shields.io/badge/license-MIT-16a34a)](../LICENSE)
[![Documentation languages: 10](https://img.shields.io/badge/docs-10%20languages-7c3aed)](../README.md#documentation)
[![GitHub source](https://img.shields.io/badge/GitHub-pangxin12345%2Fseo--delivery--guard-181717?logo=github&logoColor=white)](https://github.com/pangxin12345/seo-delivery-guard)
[![Official website](https://img.shields.io/badge/website-once--email.com-0f766e?logo=googlechrome&logoColor=white)](https://once-email.com)
[![skills.sh](https://skills.sh/b/pangxin12345/seo-delivery-guard)](https://skills.sh/pangxin12345/seo-delivery-guard)

[English](../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português do Brasil](README.pt-BR.md) · [Deutsch](README.de.md) · [Français](README.fr.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Bahasa Indonesia](README.id.md) · [Tiếng Việt](README.vi.md)

SEO 감사는 문제를 발견합니다. **SEO Delivery Guard는 AI 코딩 에이전트가 채택된 발견 사항을 구현, 검토, 릴리스, 운영 검증까지 이어 가도록 돕습니다.**

크롤러, 성능 도구, 콘텐츠 분석, 구조화 데이터 검증기, SERP 조사, Search Console 데이터를 대체하지 않습니다. 사용 가능한 기능을 조율하고 프로젝트 규칙을 적용하며, 릴리스를 막아야 하는 문제와 선택적 개선 제안을 구분합니다.

## 필요한 이유

- 소스에서 올바른 canonical이 생성 결과에서는 잘못될 수 있습니다.
- 전문 검토를 마치지 않은 번역이 Sitemap에 먼저 들어갈 수 있습니다.
- 구조화 데이터가 사용자가 볼 수 없는 사실을 설명할 수 있습니다.
- robots 지시가 접근 제어로 오해될 수 있습니다.
- 종합 점수가 색인 또는 개인정보 보호 차단 문제를 숨길 수 있습니다.
- 후보 버전은 통과하지만 운영 환경이 다른 메타데이터를 제공할 수 있습니다.
- 검색 엔진이 다시 크롤링하기 전에 성공으로 선언할 수 있습니다.

## 핵심 기능

- 변경 범위에 맞는 최소 SEO 분석 조합을 선택합니다.
- 개발, 개인정보 보호, 현지화, 분석, 광고, 테스트, 릴리스에 대한 프로젝트 규칙을 읽습니다.
- 명확한 권한 순서에 따라 충돌하는 권고를 조정합니다.
- 증거 출처, 시각, 신뢰도, 심각도, 조치, 검증 계층, 롤백 영향을 기록합니다.
- 하드 블로커를 평균 점수로 약화하지 않습니다.
- 변경 전후의 검색 노출 계약을 비교합니다.
- 소스, 생성물, 브라우저, 공개 HTTP, 실험실 결과, 자사 데이터, 제3자 추정치를 구분합니다.
- 색인, 순위, 트래픽, 리치 결과, 광고 검토, AI 노출은 검증 전까지 보류 상태로 유지합니다.
- 콘텐츠나 URL을 유지, 개선, 병합, `noindex`, 삭제 중 하나로 명확히 결정하고, 실제로 동등한 대상이 있을 때만 301을 사용하며 그렇지 않으면 정직한 `404/410`을 유지합니다.

## 하지 않는 일

- 또 다른 사이트 크롤러나 올인원 SEO 감사가 아닙니다.
- 특정 공급자, API, MCP 또는 보조 Skill을 요구하지 않습니다.
- 작업 권한 없이 URL 제출, 속성 변경, 코드 공개 또는 배포를 하지 않습니다.
- 색인, 순위, 트래픽, 리치 결과, 광고 승인 또는 AI 인용을 보장하지 않습니다.

## 입력, 출력 및 거부 경계

필요한 공개 URL, 저장소 경로, 변경 의도, 대상 사용자, 색인 의도, 언어, 정제된 증거만 제공하세요. 비밀번호, Cookie, 개인 키, 전체 분석 내보내기 또는 민감한 데이터를 제공하지 마세요. 출력은 규칙, 블로커, 조언, 미확인 항목, 증거 한계, 조치, 검증 계층, 운영 상태, 보류 중인 외부 결과를 구분합니다.

순위 조작, 조작된 경험이나 증거, 도어웨이 페이지, 가치 없는 대량 콘텐츠, 접근 제어 우회, 민감 정보 노출, 허위 인증 요청을 거부합니다. 페이지나 분석기를 사용할 수 없으면 미확인으로 유지하며 통과로 처리하지 않습니다.

각 색인 가능 페이지는 기존의 가장 강한 URL이 해결하지 못하는 작업을 해결해야 합니다. 기계 번역과 구조 검사는 언어 품질을 증명하지 못하며, 각 공개 언어 버전에는 사실과 표현 검토가 필요합니다.

## 설치

지원되는 Skill 마켓에서 설치하거나 전체 `seo-delivery-guard` 폴더를 AI 에이전트가 인식하는 Skill 디렉터리에 복사합니다. Skill을 다시 불러오거나 새 세션을 시작한 뒤 호출합니다.

```text
$seo-delivery-guard
```

공개 패키지는 텍스트 지침과 메타데이터만 포함하며 실행 파일, 크롤러, API 키 또는 운영체제 전용 구성 요소가 없습니다.

## Google Search 경계

Google Search 관련 결론은 최신 공식 문서 또는 검증된 자사 속성 데이터를 사용해야 합니다. 제3자 도구는 단서를 제공할 수 있지만 Google의 색인 결정, 순위 요인, 리치 결과 또는 AI 기능을 정의하지 않습니다.

SEO Delivery Guard는 독립적인 오픈 소스 프로젝트이며 Google과 제휴, 인증, 후원 또는 보증 관계가 없습니다.

## 게시자

- 게시자 및 공식 사이트: [once-email.com](https://once-email.com)
- 제작자: helen.jar
- GitHub: [pangxin12345](https://github.com/pangxin12345)
- 공개 지원: [tiantuowl@gmail.com](mailto:tiantuowl@gmail.com)

MIT License · 버전 0.1.0

변경 내용은 [CHANGELOG.md](../CHANGELOG.md)를 참조하세요.
