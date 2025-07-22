/* ===== router ===== */
// 다양한 라우터를 모아 관리하는 파일
import { Router } from 'express';
import TestRouter from './test'; // 테스트 라우터를 가져옴
import UserRouter from './user';

const router = Router();

// '/test' 경로로 들어오는 요청을 TestRouter로 전달
router.use('/test', TestRouter);
router.use('/user', UserRouter);

export default router;