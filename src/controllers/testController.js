/* ===== controllers ====== */
// 요청을 처리하는 로직 작성

/* ===== MVC 패턴 ===== */
// Model - View - Controller
// 요청을 처리할 때 모델(Model), 컨트롤러(Controller), 서비스(Service)를 분리하는 구조
// Controller: 클라이언트의 요청을 받고, 어떤 동작을 할지 결정한 뒤 서비스나 모델과 통신
// Service: 비즈니스 로직을 처리하고, 모델과 상호작용하며 컨트롤러에 데이터를 반환
// Model: 데이터베이스와 직접 상호작용하는 역할 (본 템플릿에선 생략)

/* ===== 서비스에서 함수 가져오기 ===== */
import { testService } from '../service/testService';

/* ===== 함수 작성 ===== */
export const getTest = async (req, res) => {
    try {
        // 서비스에서 로직을 처리한 결과를 받아옴
        const data = await testService();

        // 클라이언트에게 성공적으로 응답을 보냄
        res.status(200).json({
            status: 200, // 응답의 상태 코드로, 200은 성공을 의미
            message: 'Backend 연결 테스트 성공!', // 응답 메시지
            data: data, // data 필드에 해당 데이터를 보냄
        });
    } catch (error) {
        // 에러가 발생하면 500번 상태 코드를 클라이언트에게 반환
        res.status(500).json({
            status: 500,
            message: '서버 오류',
            error: error.message,
        });
    }
};

/* ===== 주요 개념 ===== */
// 'req'(request): 클라이언트에서 서버로 들어오는 요청(request)을 의미
// 'res'(response): 서버에서 클라이언트로 보내는 응답(response)을 의미

// 'res.status(200)': 상태 코드를 설정하는 부분, 여기서는 200번(성공)을 설정
// 'json()': 클라이언트에게 JSON 형식으로 응답을 보냄
// 'async/await'(비동기 함수): 데이터베이스 같은 외부 작업이 완료되기까지 기다려야 할 때 사용하며,
//                          이 함수가 끝날 때까지 기다리기 위해 'await'를 사용함

/* ===== status ===== */
// status는 'HTTP 상태 코드'를 나타내는 표준
// HTTP 상태 코드는 클라이언트(예: 웹 브라우저)에서 서버에 요청을 보낸 후, 서버가 그 요청을 처리한 결과를 숫자로 표현한 것
// 200 (OK): 요청이 성공적으로 처리
// 400 (Bad Request): 잘못된 요청을 보냈다는 의미
// 401 (Unauthorized): 인증이 필요하다는 의미
// 404 (Not Found): 요청한 리소스를 찾을 수 없다는 의미
// 500 (Internal Server Error: 서버에서 문제가 발생했다는 의미