import db from '../DB';

export class UserService {

    // 회원 전체 조회
    async getUsers() {
        try {
            const getQuery = 'SELECT * FROM User';
            const [data] = await db.query(getQuery);

            return data;
        } catch (e) {
            console.log(`[UserService][getUsers] Error: ${e.message}`);
        }
    };

    // 회원 단일 조회
    async getOneUser(user_id) {
        try {
            const getOneQuery = 'SELECT * FROM User WHERE user_id = ?';
            const [[data]] = await db.query(getOneQuery, user_id);

            return data;
        } catch (e) {
            console.log(`[UserService][getOneUser] Error: ${e.message}`);
        }
    };

    // 로그인
    async signIn(userInfo) {
        try {
            const { id, password } = userInfo;

            // 아이디가 존재하는지 확인
            const getQuery = 'SELECT * FROM User WHERE id = ?';
            const [[user]] = await db.query(getQuery, [id]);

            // 아이디가 존재하지 않으면 에러
            if (!user) {
                throw new Error('Invalid Id');
            }

            // 비밀번호가 틀리면 에러
            if (user.password != password) {
                throw new Error('Wrong Password');
            }

            // 넘겨줄 데이터를 정함 (id, name 말고도 다른 데이터 추가 가능)
            const data = {
                id: user.id,
                name: user.name,
            };

            return data;

        } catch (e) {
            console.log(`[UserService][signIn] Error: ${e.message}`);
        }
    };

    // 로그인
    async signUp(userInfo) {
        try {

            const { id, password, name } = userInfo;

            // 아이디 중복 확인
            const getQuery = 'SELECT * FROM User WHERE id = ?';
            const [[user]] = await db.query(getQuery, [id]);

            if (user) {
                throw new Error('Already has User');
            }

            // 회원가입
            const postQuery = 'INSERT INTO User(id, password, name) VALUES (?, ?, ?)';
            const [data] = await db.query(postQuery, [id, password, name]);

            return data;

        } catch (e) {
            console.log(`[UserService][signUp] Error: ${e.message}`);
        }
    }
};