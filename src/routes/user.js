import express from "express";
import { getOneUser, getUsers, signIn, signUp } from "../controllers/userController";

const router = express.Router();

/* ===== GET ===== */
router.get('/', getUsers);
router.get('/:id', getOneUser);

/* ===== POST ===== */
router.post('/signin', signIn);
router.post('/signup', signUp);

export default router;