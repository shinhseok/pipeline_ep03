# Hook 제작 옵션 — Content Planner Reference

---

## Hook 타입 (HOOK_TYPE)

| 값 | 설명 |
|----|------|
| `standard` (기본) | 기존 나레이션 Hook — 변경 없음 |
| `song` | 30초 싱어송라이터 노래 Hook — Shorts 듀얼 활용 |

**Song Hook 선택 시 추가 기술:**
- **가사 컨셉**: 에피소드 주제를 유머러스하게 요약하는 방향
- **톤**: 웃긴 싱어송라이터, 자기비하적, 기타 반주
- **시그니처 멜로디**: 채널 공통 멜로디(Suno 생성) — 가사만 에피소드별 변경
- **브릿지 설계**: 노래 → 나레이션 전환 방법 (후크라인 질문화 → 침묵 → 나레이션)
- **가사 분량**: 80~120 음절, 6~10줄 (중간 템포 ~4음절/초 × 30초)

---

## Hook 미디어 (HOOK_MEDIA)

| 값 | 설명 |
|----|------|
| `image` (기본) | 기존 정적 이미지 + 나레이션 |
| `video` | Veo3/Kling 영상 클립 — Start/End 이미지 + 모션 프롬프트 |

**Video Hook 선택 시 추가 기술:**
- **영상 엔진**: `veo3` (기본) / `kling`
- **연출 모드 선택**:
  - **Kinetic Transition (권장)**: 연속 KF 이미지를 start/end로 사용. 캐릭터 이동+모션 블러로 장면 전환. 원테이크 서사, 시대 관통 Hook에 적합
  - **Per-Shot (레거시)**: Shot별 start/end 이미지 분리. 단일 Shot 내 상태 변화에 적합
- **최소 Shot 수**: Kinetic Transition 선택 시 **최소 5 Shot** (영상 4개 + landing frame 1개). 30초 Hook에 충분한 시각적 리듬을 확보하기 위함.
- **이미지 생성 우선순위**: Hook 이미지가 영상 생성의 입력이므로 Phase 0으로 우선 생성

---

## 4가지 조합

| HOOK_TYPE | HOOK_MEDIA | 결과 |
|-----------|-----------|------|
| standard | image | 기존 방식 (나레이션 + 이미지) |
| standard | video | 나레이션 + 영상 클립 |
| song | image | 노래 + 이미지 |
| song | video | 노래 + 영상 클립 (최대 임팩트) |
