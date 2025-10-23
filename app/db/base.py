from sqlalchemy.orm import declarative_base

Base = declarative_base()

# Import *modules*, not classes
import app.db.models.user  # noqa
import app.db.models.job_description  # noqa
import app.db.models.persona  # noqa
import app.db.models.candidate  # noqa
import app.db.models.score  # noqa
import app.db.models.role  # noqa
import app.db.models.company  # noqa
import app.db.models.job_role  # noqa
import app.db.models.mfa  # noqa
