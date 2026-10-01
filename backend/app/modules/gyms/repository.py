from app.core.repository import TenantRepository
from app.modules.gyms.models import Branch, Invite, StaffMembership


class BranchRepository(TenantRepository[Branch]):
    model = Branch


class StaffRepository(TenantRepository[StaffMembership]):
    model = StaffMembership


class InviteRepository(TenantRepository[Invite]):
    model = Invite
