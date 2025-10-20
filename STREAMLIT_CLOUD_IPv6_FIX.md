# Streamlit Cloud IPv6 연결 문제 해결

## 문제

**Streamlit Cloud는 IPv6를 지원하지 않습니다**

로그에서 발견된 에러:
```
connection to server at "db.hfaucafjyxyrzhhlcyvy.supabase.co" (2406:da12:...),
port 5432 failed: Cannot assign requested address
```

Supabase 호스트가 IPv6 주소로 resolve되어 연결 실패.

---

## 해결책 1: Supabase IPv4 Pooler 사용 (권장)

Supabase는 **Transaction Pooler**를 제공하며, IPv4 전용입니다.

### Streamlit Cloud Secrets 수정

기존:
```toml
SUPABASE_URL = "postgresql://postgres:devswha1!@db.hfaucafjyxyrzhhlcyvy.supabase.co:5432/postgres"
```

**새로운 (Pooler 사용)**:
```toml
SUPABASE_URL = "postgresql://postgres.hfaucafjyxyrzhhlcyvy:devswha1!@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres"
```

### 변경 사항:
1. **호스트**: `db.xxx.supabase.co` → `aws-0-ap-northeast-2.pooler.supabase.com`
2. **포트**: `5432` → `6543`
3. **사용자명**: `postgres` → `postgres.hfaucafjyxyrzhhlcyvy`

### 장점:
- IPv4 전용
- Connection pooling으로 성능 향상
- Streamlit Cloud 무료 티어의 connection limit에 안전

---

## 해결책 2: Supabase Direct Connection IPv4 주소 사용

Supabase 대시보드에서 IPv4 주소를 직접 얻어서 사용:

1. Supabase Dashboard → Project Settings → Database
2. "Connection string" 섹션에서 "URI" 복사
3. 호스트 부분만 IPv4 주소로 교체

**주의**: IP 주소는 변경될 수 있으므로 권장하지 않음.

---

## Supabase Connection Pooler 설정 가이드

### 1. Pooler URL 찾기

Supabase Dashboard:
1. **Project Settings** → **Database**
2. **Connection Pooling** 섹션
3. **Transaction mode** 선택
4. **Connection string** 복사

형식:
```
postgresql://postgres.PROJECT:PASSWORD@REGION.pooler.supabase.com:6543/postgres
```

### 2. Streamlit Cloud Secrets 업데이트

1. https://share.streamlit.io/ 접속
2. Horcrux 앱 → Settings → Secrets
3. `SUPABASE_URL` 교체:
```toml
SUPABASE_URL = "복사한 Pooler URL"
```
4. Save → 앱 자동 재시작

---

## 검증

재배포 후 디버그 패널 확인:
- **DB 타입**: `postgres` ✅
- **PostgreSQL 연결 실패**: 메시지 없음 ✅

---

## 참고

### Transaction Pooler vs Direct Connection

| 항목 | Direct (5432) | Pooler (6543) |
|------|---------------|---------------|
| IPv6 | ✅ | ❌ (IPv4만) |
| Connection Limit | 낮음 | 높음 |
| 지연 시간 | 낮음 | 약간 높음 |
| Streamlit Cloud | ❌ | ✅ |

### Supabase 문서
- [Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [IPv6 Support](https://github.com/orgs/supabase/discussions/1928)

---

## 현재 상태

- ❌ Direct connection (5432) - IPv6 문제로 실패
- ⏳ Pooler connection (6543) - 설정 필요

**다음 단계**: Supabase Pooler URL로 변경
