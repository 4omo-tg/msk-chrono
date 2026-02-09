from app.db.base_class import Base
from app.models.user import User
from app.models.poi import PointOfInterest
from app.models.route import Route
from app.models.progress import UserProgress
from app.models.quiz import Quiz
from app.models.user_quiz_progress import UserQuizProgress
from app.models.achievement import Achievement, UserAchievement
from app.models.cosmetics import Title, UserTitle, ProfileFrame, UserFrame, Badge, UserBadge
from app.models.friendship import FriendRequest, Friendship
from app.models.time_photo import TimePhoto
from app.models.learning import (
    LearningModule, LearningLesson, LearningQuestion,
    UserLearningProgress, UserLessonProgress, UserQuestionHistory, LearningSession
)
from app.models.site_setting import SiteSetting
