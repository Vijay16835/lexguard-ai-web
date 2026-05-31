# Import all models here so that Base has them before being imported by Alembic
from app.db.session import Base # noqa
from app.models.user import User # noqa
from app.models.document import Document # noqa
from app.models.analysis import Analysis # noqa
from app.models.clause import Clause # noqa
from app.models.chat import ChatHistory # noqa
from app.models.notification import Notification # noqa
from app.models.settings import UserSettings # noqa
