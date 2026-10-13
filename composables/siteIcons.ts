import {
  Globe, Code2, Server, Workflow, Compass, Presentation, Users, MonitorPlay, LifeBuoy, Lightbulb, ShieldCheck, Award,
  Accessibility, TrendingUp, CheckCircle2, GraduationCap, Rocket, Briefcase, HeartHandshake, Sparkles, Target, Eye,
  BookOpen, Cpu, Cloud, Lock,
} from 'lucide-vue-next'

/** Icons an admin can pick for website cards (names match the API's ICONS list). */
export const SITE_ICONS: Record<string, any> = {
  globe: Globe, code: Code2, server: Server, workflow: Workflow, compass: Compass, presentation: Presentation,
  users: Users, 'monitor-play': MonitorPlay, 'life-buoy': LifeBuoy, lightbulb: Lightbulb, 'shield-check': ShieldCheck,
  award: Award, accessibility: Accessibility, 'trending-up': TrendingUp, 'check-circle': CheckCircle2,
  'graduation-cap': GraduationCap, rocket: Rocket, briefcase: Briefcase, 'heart-handshake': HeartHandshake,
  sparkles: Sparkles, target: Target, eye: Eye, 'book-open': BookOpen, cpu: Cpu, cloud: Cloud, lock: Lock,
}
