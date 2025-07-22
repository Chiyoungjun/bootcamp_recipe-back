/* ===== express-generator 사용 ===== */
// Express는 Node.js로 웹 애플리케이션(웹사이트나 API 등)을 만들기 쉽게 해주는 도구
// express-generator는 기본적인 구조와 설정을 자동으로 만들어주는 도구

/* ===== 설치 라이브러리 및 패키지 ===== */
// cors: Cross-Origin Resource의 약자로, 다른 도메인에서 이 서버에 접근할 수 있게 허용하는 도구
// mysql2: MySQL 데이터베이스에 연결해 데이터를 주고받을 수 있도록 도와주는 도구
// nodemon: 코드가 변경될 때마다 서버를 자동으로 재시작해주는 도구로, 개발할 때 편함
// morgan: 웹 브라우저가 서버에 요청할 때마다 요청 내용을 기록해주는 도구 (로깅 기능)
// babel: 최신 ES6, ES7 버전의 JavaScript 코드를 ES5 버전으로 변환해주는 도구
//        - @babel/core: babel의 핵심 파일, babel의 다른 모듈들이 종속성을 가짐
//        - @babel/cli: 터미널에서 babel을 실행할 수 있게 해주는 도구
//        - @babel/node: babel을 사용해 Node.js를 실행하게 해주는 도구
//        - @babel/preset-env: 최신 JavaScript 문법을 자동으로 변환해주는 설정

/* ===== 번외 ===== */
// node 패키지를 설치할 때, '--save-dev'를 붙이고 안붙이고의 차이?
// package.json을 보면 '--save-dev'로 설치한 패키지는 "devDependencies" 필드에 담김.
// 안붙이면: 실제 서비스 제공을 위한 코드 실행 = 배포 용도 (mysql2, ...)
// 붙이면: 개발/테스트 목적의 코드 실행 = 개발 용도 (nodemon, ...)

/* ===== express 설정을 위한 라이브러리 import ===== */
import createError from 'http-errors'; // 에러 발생 시 적절한 에러 메시지를 만들어주는 도구
import express from 'express';
import cors from 'cors';
import path from 'path'; // 파일과 디렉토리 경로를 쉽게 다룰 수 있게 해주는 도구
import cookieParser from 'cookie-parser'; // 웹 사이트에서 쿠키를 쉽게 다룰 수 있게 해주는 도구
import logger from 'morgan';





/* ===== 라우터 설정 ===== */
// 라우터는 특정 주소로 들어오는 요청을 처리하는 코드를 모아놓은 곳
import testRouter from './routes';
import userRouter from './routes';





/* ===== express 설정을 위한 변수 선언 ===== */
// app이라는 변수에 express를 사용해 서버를 만들 준비를 함
const app = express(); // const는 값이 변하지 않는 변수를 만들 때 사용함, 왠만한 모든 경우엔 const로 변수 선언

/* ===== 뷰 엔진 설정 ===== */
// 웹 페이지를 렌더링할 때 사용하는 템플릿 엔진(ejs)을 설정하는 부분
// 'views' 폴더에 템플릿 파일들이 위치하고, 'ejs'를 템플릿 엔진으로 사용한다는 의미
// 건드릴 필요 없음
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');

/* ===== express 미들웨어 설정 ====== */
// 미들웨어는 요청이 들어왔을 때 요청을 처리ㅣ하기ㅣ 전에 거쳐가는 함수들
// 로그를 기록하고, JSON 형식 데이터를 처리하며, 쿠키를 다루고, 정적 파일을 제공
app.use(logger('dev')); // morgan을 사용해 요청 기록을 남김
app.use(express.json()); // 들어온 요청이 JSON 형식일 때 이를 처리함
app.use(express.urlencoded({ extended: false })); // URL 인코딩된 데이터를 처리
app.use(cookieParser()); // 쿠키 데이터를 처리
app.use(express.static(path.join(__dirname, 'public'))); // 'public' 폴더의 파일을 정적으로 제공
app.use(cors()); // 다른 도메인에서 오는 요청 허용





/* ===== 라우터 연결 ===== */
// '/test'로 들어오는 요청은 testRouter에서 처리하고,
// '/user'로 들어오는 요청은 userRouter에서 처리함
app.use('/', testRouter);
app.use('/', userRouter);





// 이하의 코드들은 에러 처리 부분이므로 읽어보기만 하는걸 추천

/* ===== 404 에러 처리 ===== */
// 이 미들웨어는 요청한 페이지를 찾을 수 없을 때(404 에러) 이를 처리하는 함수
app.use(function(req, res, next) {
  next(createError(404)); // 404 에러를 만들어서 다음 미들웨어로 넘김
});

/* ===== 에러 핸들러 ===== */
// 에러가 발생했을 때 이를 처리하고, 에러 메시지를 클라이언트에게 보여줌
app.use(function(err, req, res, next) {
  // 에러 메시지와 환경에 따라 보여줄 에러 정보를 설정
  res.locals.message = err.message;
  res.locals.error = req.app.get('env') === 'development' ? err : {};

  // 에러 페이지를 렌더링
  res.status(err.status || 500); // 에러 상태 코드를 설정하고
  res.render('error'); // 'error'라는 템플릿 파일을 렌더링
});

/* ===== 앱을 모듈로 내보내기 ===== */
// 다른 파일에서 이 app을 불러와 사용할 수 있도록 내보내줌
module.exports = app;