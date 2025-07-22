/* ===== 라우터 파일 ===== */
// 백엔드 연결 테스트를 위한 라우터를 정의

import express from 'express';
import { getTest } from '../controllers/testController';

const router = express.Router();

// GET 요청이 오면, getTest 함수가 실행됨
router.get('/', getTest);

export default router;