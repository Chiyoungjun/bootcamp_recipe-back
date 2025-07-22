/* ===== mysql2 라이브러리 import ===== */
// 'mysql2'와 'mysql2/promise'의 차이?
// 'mysql2': 모든 기능(콜백 및 promise)를 가져옴
// 'mysql2/promise': promise 기반 MySQL 기능만 가져옴
// 즉, "비동기 처리 방식"에 다름 = await/async를 사용하고 싶다면 'promise' 방식이 필요
const mysql = require('mysql2/promise');

const DB = mysql.createPool({
    host: 'localhost',
    port: '3306',
    user: 'root',
    password: '0000',
    database: 'db_test',
});

export default DB;