# UnoLingo

#### Ceban Andrei, FAF-211

### 1. Assess application suitability
The following system is suitable for the real-time language learning app due to several reasons:

* The Learning Session Service is essential and flexible as it manages core functionalities like matching users with native speakers or tutors, handling conversation sessions (text, voice, or video), and providing real-time feedback during language practice (such as pronunciation correction, vocabulary tips, or grammar suggestions).


* Real-time interactions will occur continuously even without a distinct lobby service, necessitating scalable systems, particularly when multiple learners and tutors are engaged in live sessions simultaneously.


* To handle its specific load, each service (Learning Sessions, User Matching, and Authentication) can scale independently. For example, during peak usage hours, there may be a greater demand on the Learning Session Service to support multiple concurrent conversations.


* The system will manage learner-tutor interactions, user authentication, and real-time feedback as distinct services, much like platforms such as Netflix decouple their services to manage streaming, recommendations, and user authentication separately.


### 2. Define service boundaries