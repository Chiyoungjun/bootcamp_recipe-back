📦 SNAP COOK - Backend API (AI & ML Orchestration)

**SNAP COOK의 핵심 지능형 로직을 담당하는 백엔드 서버입니다. 
컴퓨터 비전(YOLO11), 머신러닝(Random Forest), 공공 데이터 OpenAPI를 통합하여 지능형 레시피 큐레이션을 실현했습니다.**

🔗 Repository URL
- https://github.com/Chiyoungjun/bootcamp_recipe-back/tree/new_young_back

**🛠 Tech Stack & Core AI**
- **Runtime**: Node.js / Express.js (FastAPI 연동)
- **Database**: MySQL / Sequelize
- **Computer Vision**: YOLO11 (음식 이미지 학습 및 실시간 객체 탐지)
- **Machine Learning**: Scikit-learn (Random Forest 모델을 활용한 BMI 분류)
- **External API**: 
    - 식품안전나라 OpenAPI (표준 레시피 및 영양 정보 연동)
    - AI Chat & Translation API (챗봇 및 다국어 번역)

🌟 핵심 구현 기능
1. **YOLO11 기반 음식 탐지**: 직접 학습시킨 모델을 통해 이미지 내 음식의 위치와 종류를 정확히 예측하며, 학습 손실을 최소화하여 높은 성능(mAP)을 달성했습니다.
2. **BMI 기반 맞춤형 추천 엔진**: 
   - 랜덤 포레스트 모델을 활용해 약 84%의 정확도로 사용자 체형을 분류합니다.
   - 분류된 상태에 따라 최적의 영양학적 레시피를 매핑하여 제공하는 알고리즘을 설계했습니다.
3. **데이터 파이프라인 구축**: 식품안전나라 OpenAPI를 연동하여 대량의 레시피 데이터를 안정적으로 처리하고 DB화했습니다.
4. **지능형 카테고리 최적화**: 9개의 음식 카테고리 분류 모델을 통해 검색 및 추천의 정확도를 개선했습니다.
5. **보안 및 환경 관리**: API Key와 DB 접속 정보를 `.env`로 엄격히 관리하여 보안성을 확보했습니다.

## 🚀 기술적 성과
- **AI 파이프라인 통합**: 단순히 외부 기능을 가져오는 것에 그치지 않고, 직접 모델을 학습시키고 서비스에 서빙하는 전체 과정을 주도했습니다.
- **RESTful API 설계**: 프론트엔드와의 원활한 협업을 위해 자원 중심의 엔드포인트를 설계하고 일관된 응답 구조를 유지했습니다.
