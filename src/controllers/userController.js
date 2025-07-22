import { UserService } from '../service/userService';


// 회원 전체 조회
export const getUsers = async (req, res) => {
    try {
        const userService = new UserService();
        const data = await userService.getUsers();

        return res.status(200).json({
            status: 200,
            message: 'success',
            data: data,
        });
    } catch (e) {
        return res.status(500).json({
            status: 500,
            message: 'server error',
            data: e.message,
        });
    }
};


// 회원 단일 조회
export const getOneUser = async (req, res) => {
    try {
        const userService = new UserService();
        const data = await userService.getOneUser();

        return res.status(200).json({
            status: 200,
            message: 'success',
            data: data,
        });
    } catch (e) {
        return res.status(500).json({
            status: 500,
            message: 'server error',
            data: e.message,
        });
    }
};

// 회원 가입
export const signUp = async (req, res) => {
    try {
        const userService = new UserService();
        const data = await userService.signUp(req.body);

        return res.status(200).json({
            status: 200,
            message: 'success',
            data: data,
        });
    } catch (e) {
        return res.status(500).json({
            status: 500,
            message: 'server error',
            data: e.message,
        });
    }
};

// 로그인
export const signIn = async (req, res) => {
    try {
        const userService = new UserService();
        const data = await userService.signIn(req.body);

        return res.status(200).json({
            status: 200,
            message: 'success',
            data: data,
        });
    } catch (e) {
        return res.status(500).json({
            status: 500,
            message: 'server error',
            data: e.message,
        });
    }
};