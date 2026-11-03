import ApprovalInbox from './approvals/ApprovalInbox.vue'
import DashboardScreen from './dashboard/DashboardScreen.vue'
import DrawingList from './drawings/DrawingList.vue'
import HullList from './hulls/HullList.vue'
import PlanGantt from './plans/PlanGantt.vue'
import ProgressScreen from './progress/ProgressScreen.vue'
import UserManagement from './users/UserManagement.vue'

// Screen token -> owning feature. Real screens replace the placeholder in their feature phase.
export const SCREENS = {
  dashboard: 'F03', 'hull-list': 'F04', 'plan-gantt': 'F05', progress: 'F06',
  'dwg-list': 'F07', 'dwg-approval': 'F08', 'user-mgmt': 'F09',
}

// Implemented screens (others render ScreenPlaceholder)
export const SCREEN_COMPONENTS = { dashboard: DashboardScreen, 'hull-list': HullList, 'plan-gantt': PlanGantt, progress: ProgressScreen, 'dwg-list': DrawingList, 'dwg-approval': ApprovalInbox, 'user-mgmt': UserManagement }
