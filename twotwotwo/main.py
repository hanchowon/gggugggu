import hashlib
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Hash Search Algorithm Server")

# ==========================================
# 1. CORS 설정 (모든 오리진 허용)
# GAS(Google Apps Script)와의 연동을 위해 통신 허용 설정
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # GAS 환경 및 웹 요청 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# 2. Chaining 방식 해시 테이블 구현
# ==========================================
class Node:

    def __init__(self, key: Any, value: Any, next_node: Optional["Node"] = None):
        self.key = key
        self.value = value
        self.next = next_node


class ChainedHash:

    def __init__(self, capacity: int = 13):
        self.capacity = capacity
        self.table: List[Optional[Node]] = [None] * self.capacity

    def hash_value(self, key: Any) -> int:
        """키의 해시값을 구하여 테이블 인덱스로 변환 (hash_value 기능)"""
        if isinstance(key, int):
            return key % self.capacity
        # 문자열 등 기타 타입은 SHA-256을 활용해 정수로 변환 후 해싱
        key_bytes = str(key).encode("utf-8")
        return int(hashlib.sha256(key_bytes).hexdigest(), 16) % self.capacity

    def search(self, key: Any) -> Any:
        """키로 값을 검색 (search 기능)"""
        idx = self.hash_value(key)
        p = self.table[idx]

        while p is not None:
            if p.key == key:
                return p.value
            p = p.next
        return None

    def add(self, key: Any, value: Any) -> bool:
        """키와 값을 추가 (add 기능 - 중복 키 허용 안 함)"""
        idx = self.hash_value(key)
        p = self.table[idx]

        while p is not None:
            if p.key == key:
                p.value = value  # 이미 존재하면 값 업데이트
                return False
            p = p.next

        # 노드 삽입 (리스트의 맨 앞에 추가)
        temp = Node(key, value, self.table[idx])
        self.table[idx] = temp
        return True

    def remove(self, key: Any) -> bool:
        """키에 해당하는 노드 삭제 (remove 기능)"""
        idx = self.hash_value(key)
        p = self.table[idx]
        prev = None

        while p is not None:
            if p.key == key:
                if prev is None:
                    self.table[idx] = p.next
                else:
                    prev.next = p.next
                return True
            prev = p
            p = p.next
        return False

    def dump(self) -> Dict[int, List[Dict[str, Any]]]:
        """해시 테이블 전체 상태를 출력 가능하도록 변환 (dump 기능)"""
        result = {}
        for i in range(self.capacity):
            bucket = []
            p = self.table[i]
            while p is not None:
                bucket.append({"key": p.key, "value": p.value})
                p = p.next
            result[i] = bucket
        return result


# 메모리 상에서 동작할 글로벌 해시 테이블 객체
hash_table: Optional[ChainedHash] = None


# ==========================================
# 3. Request/Response 데이터 모델 (Pydantic)
# ==========================================
class InitRequest(BaseModel):
    capacity: int = 13


class AddRequest(BaseModel):
    key: Any
    value: Any


class SearchRequest(BaseModel):
    key: Any


class RemoveRequest(BaseModel):
    key: Any


class HashValueRequest(BaseModel):
    key: Any


# ==========================================
# 4. API Endpoints
# ==========================================
@app.get("/")
def read_root():
    return {"message": "Hash Search Algorithm Server is running."}


@app.post("/init")
def api_init(req: InitRequest):
    """해시 테이블 초기화 (init)"""
    global hash_table
    if req.capacity <= 0:
        raise HTTPException(status_code=400, detail="Capacity must be > 0.")
    hash_table = ChainedHash(capacity=req.capacity)
    return {
        "status": "success",
        "message": f"Hash table initialized with capacity {req.capacity}.",
    }


def _check_table_initialized():
    if hash_table is None:
        raise HTTPException(
            status_code=400,
            detail="Hash table is not initialized. Call /init first.",
        )


@app.post("/hash_value")
def api_hash_value(req: HashValueRequest):
    """특정 키의 해시 인덱스 계산 (hash_value)"""
    _check_table_initialized()
    idx = hash_table.hash_value(req.key)
    return {"key": req.key, "hash_index": idx}


@app.post("/add")
def api_add(req: AddRequest):
    """데이터 추가/업데이트 (add)"""
    _check_table_initialized()
    is_new = hash_table.add(req.key, req.value)
    idx = hash_table.hash_value(req.key)
    action = "added" if is_new else "updated"
    return {
        "status": "success",
        "action": action,
        "key": req.key,
        "value": req.value,
        "hash_index": idx,
    }


@app.post("/search")
def api_search(req: SearchRequest):
    """데이터 검색 (search)"""
    _check_table_initialized()
    val = hash_table.search(req.key)
    if val is None:
        return {"found": False, "key": req.key, "value": None}
    return {
        "found": True,
        "key": req.key,
        "value": val,
        "hash_index": hash_table.hash_value(req.key),
    }


@app.post("/remove")
def api_remove(req: RemoveRequest):
    """데이터 삭제 (remove)"""
    _check_table_initialized()
    success = hash_table.remove(req.key)
    if not success:
        raise HTTPException(status_code=44, detail="Key not found.")
    return {"status": "success", "message": f"Key '{req.key}' removed."}


@app.get("/dump")
def api_dump():
    """해시 테이블의 모든 내용 및 버킷 상태 반환 (dump)"""
    _check_table_initialized()
    return {"capacity": hash_table.capacity, "table": hash_table.dump()}
