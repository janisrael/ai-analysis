#!/usr/bin/env python3
"""
AI Avatar Assistant - Project Templates & Quick-Start Wizards
Comprehensive templates for rapid project initialization and estimation
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

class ProjectType(Enum):
    """Types of projects"""
    WEB_APPLICATION = "web_application"
    MOBILE_APP = "mobile_app"
    DESKTOP_APP = "desktop_app"
    API_SERVICE = "api_service"
    MICROSERVICE = "microservice"
    DATA_SCIENCE = "data_science"
    MACHINE_LEARNING = "machine_learning"
    BLOCKCHAIN = "blockchain"
    GAME_DEVELOPMENT = "game_development"
    DEVOPS_INFRASTRUCTURE = "devops_infrastructure"
    E_COMMERCE = "e_commerce"
    CMS_WEBSITE = "cms_website"
    CUSTOM = "custom"

class ProjectComplexity(Enum):
    """Project complexity levels"""
    SIMPLE = "simple"        # Basic functionality, single developer
    MEDIUM = "medium"        # Standard features, small team
    COMPLEX = "complex"      # Advanced features, larger team
    ENTERPRISE = "enterprise" # Large-scale, multiple teams

class TechnologyStack(Enum):
    """Common technology stacks"""
    REACT_NODE = "react_node"
    VUE_EXPRESS = "vue_express"
    ANGULAR_DOTNET = "angular_dotnet"
    PYTHON_DJANGO = "python_django"
    PYTHON_FLASK = "python_flask"
    REACT_NATIVE = "react_native"
    FLUTTER = "flutter"
    NEXT_JS = "next_js"
    NUXT_JS = "nuxt_js"
    SVELTE_KIT = "svelte_kit"
    SPRING_BOOT = "spring_boot"
    LARAVEL_PHP = "laravel_php"
    RUBY_RAILS = "ruby_rails"
    GOLANG_GIN = "golang_gin"

@dataclass
class ProjectRequirement:
    """Individual project requirement"""
    id: str
    name: str
    description: str
    category: str  # "core", "feature", "integration", "deployment"
    priority: str  # "must_have", "should_have", "could_have", "wont_have"
    estimated_hours: float
    dependencies: List[str]
    technologies: List[str]

@dataclass
class ProjectTemplate:
    """Complete project template"""
    id: str
    name: str
    description: str
    project_type: ProjectType
    complexity: ProjectComplexity
    technology_stack: TechnologyStack
    estimated_duration_weeks: float
    team_size_recommended: int
    requirements: List[ProjectRequirement]
    phases: List[Dict[str, Any]]
    risk_factors: List[str]
    deliverables: List[str]
    success_criteria: List[str]
    created_at: datetime
    updated_at: datetime

@dataclass
class QuickStartWizardStep:
    """Step in quick-start wizard"""
    id: str
    title: str
    description: str
    step_type: str  # "selection", "input", "configuration", "confirmation"
    options: Optional[List[Dict[str, Any]]] = None
    validation: Optional[Dict[str, Any]] = None
    dependencies: Optional[List[str]] = None

@dataclass
class ProjectEstimate:
    """Generated project estimate"""
    project_id: str
    template_id: str
    total_hours: float
    total_cost: float
    duration_weeks: float
    team_composition: Dict[str, int]
    phase_breakdown: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    generated_at: datetime

class ProjectTemplateManager:
    """Manages project templates and quick-start wizards"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.templates: Dict[str, ProjectTemplate] = {}
        self.wizard_steps: Dict[str, List[QuickStartWizardStep]] = {}
        self.templates_file = "data/project_templates.json"
        self.load_templates()
        self.initialize_default_templates()
    
    def load_templates(self):
        """Load templates from file"""
        try:
            if os.path.exists(self.templates_file):
                with open(self.templates_file, 'r') as f:
                    data = json.load(f)
                
                for template_data in data.get('templates', []):
                    template = ProjectTemplate(**template_data)
                    self.templates[template.id] = template
                
                self.logger.info(f"Loaded {len(self.templates)} project templates")
        except Exception as e:
            self.logger.error(f"Failed to load templates: {e}")
    
    def save_templates(self):
        """Save templates to file"""
        try:
            os.makedirs(os.path.dirname(self.templates_file), exist_ok=True)
            
            data = {
                "templates": [asdict(template) for template in self.templates.values()],
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.templates_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.info("Templates saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save templates: {e}")
    
    def initialize_default_templates(self):
        """Initialize default project templates"""
        if not self.templates:
            default_templates = self._create_default_templates()
            for template in default_templates:
                self.templates[template.id] = template
            self.save_templates()
    
    def _create_default_templates(self) -> List[ProjectTemplate]:
        """Create default project templates"""
        templates = []
        
        # React E-commerce Template
        react_ecommerce = ProjectTemplate(
            id="react_ecommerce_complex",
            name="React E-commerce Platform",
            description="Full-featured e-commerce platform with React frontend and Node.js backend",
            project_type=ProjectType.E_COMMERCE,
            complexity=ProjectComplexity.COMPLEX,
            technology_stack=TechnologyStack.REACT_NODE,
            estimated_duration_weeks=16,
            team_size_recommended=4,
            requirements=[
                ProjectRequirement(
                    id="user_auth",
                    name="User Authentication & Authorization",
                    description="User registration, login, password reset, role-based access",
                    category="core",
                    priority="must_have",
                    estimated_hours=80,
                    dependencies=[],
                    technologies=["JWT", "bcrypt", "OAuth"]
                ),
                ProjectRequirement(
                    id="product_catalog",
                    name="Product Catalog Management",
                    description="Product listing, search, filtering, categories",
                    category="core",
                    priority="must_have",
                    estimated_hours=120,
                    dependencies=["user_auth"],
                    technologies=["Elasticsearch", "React", "Node.js"]
                ),
                ProjectRequirement(
                    id="shopping_cart",
                    name="Shopping Cart & Checkout",
                    description="Add to cart, cart management, checkout process",
                    category="core",
                    priority="must_have",
                    estimated_hours=100,
                    dependencies=["product_catalog", "user_auth"],
                    technologies=["React Context", "localStorage"]
                ),
                ProjectRequirement(
                    id="payment_integration",
                    name="Payment Processing",
                    description="Stripe/PayPal integration, payment handling",
                    category="feature",
                    priority="must_have",
                    estimated_hours=80,
                    dependencies=["shopping_cart"],
                    technologies=["Stripe API", "PayPal SDK"]
                ),
                ProjectRequirement(
                    id="admin_panel",
                    name="Admin Dashboard",
                    description="Product management, order tracking, analytics",
                    category="feature",
                    priority="should_have",
                    estimated_hours=120,
                    dependencies=["user_auth"],
                    technologies=["React Admin", "Chart.js"]
                ),
                ProjectRequirement(
                    id="responsive_design",
                    name="Mobile Responsive Design",
                    description="Mobile-first responsive design implementation",
                    category="feature",
                    priority="must_have",
                    estimated_hours=60,
                    dependencies=["product_catalog"],
                    technologies=["CSS Grid", "Flexbox", "Material-UI"]
                ),
                ProjectRequirement(
                    id="deployment",
                    name="Production Deployment",
                    description="CI/CD pipeline, hosting setup, monitoring",
                    category="deployment",
                    priority="must_have",
                    estimated_hours=40,
                    dependencies=["admin_panel", "payment_integration"],
                    technologies=["Docker", "AWS/Vercel", "GitHub Actions"]
                )
            ],
            phases=[
                {
                    "name": "Planning & Setup",
                    "duration_weeks": 2,
                    "tasks": ["Project setup", "Architecture design", "Database schema"],
                    "deliverables": ["Project structure", "Technical specifications"]
                },
                {
                    "name": "Core Development",
                    "duration_weeks": 8,
                    "tasks": ["Authentication", "Product catalog", "Shopping cart"],
                    "deliverables": ["Working MVP", "Core functionality"]
                },
                {
                    "name": "Advanced Features",
                    "duration_weeks": 4,
                    "tasks": ["Payment integration", "Admin panel", "Advanced features"],
                    "deliverables": ["Complete platform", "Admin tools"]
                },
                {
                    "name": "Testing & Deployment",
                    "duration_weeks": 2,
                    "tasks": ["Testing", "Performance optimization", "Deployment"],
                    "deliverables": ["Production-ready application", "Documentation"]
                }
            ],
            risk_factors=[
                "Payment gateway integration complexity",
                "Performance with large product catalogs",
                "Security vulnerabilities in payment handling",
                "Mobile responsiveness challenges"
            ],
            deliverables=[
                "React frontend application",
                "Node.js backend API",
                "Admin dashboard",
                "Mobile-responsive design",
                "Payment integration",
                "Deployment pipeline",
                "Technical documentation"
            ],
            success_criteria=[
                "Users can browse and purchase products",
                "Payment processing works reliably",
                "Admin can manage products and orders",
                "Site loads under 3 seconds",
                "Mobile experience is seamless"
            ],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        templates.append(react_ecommerce)
        
        # React Native Mobile App Template
        react_native_app = ProjectTemplate(
            id="react_native_social",
            name="React Native Social App",
            description="Social media mobile app with real-time features",
            project_type=ProjectType.MOBILE_APP,
            complexity=ProjectComplexity.MEDIUM,
            technology_stack=TechnologyStack.REACT_NATIVE,
            estimated_duration_weeks=12,
            team_size_recommended=3,
            requirements=[
                ProjectRequirement(
                    id="user_profiles",
                    name="User Profiles & Authentication",
                    description="User registration, profiles, social login",
                    category="core",
                    priority="must_have",
                    estimated_hours=60,
                    dependencies=[],
                    technologies=["Firebase Auth", "React Native"]
                ),
                ProjectRequirement(
                    id="real_time_chat",
                    name="Real-time Messaging",
                    description="Chat functionality with real-time updates",
                    category="core",
                    priority="must_have",
                    estimated_hours=80,
                    dependencies=["user_profiles"],
                    technologies=["Socket.io", "Firebase Firestore"]
                ),
                ProjectRequirement(
                    id="social_features",
                    name="Social Features",
                    description="Posts, likes, comments, friend system",
                    category="feature",
                    priority="should_have",
                    estimated_hours=100,
                    dependencies=["user_profiles"],
                    technologies=["React Native", "Firebase"]
                ),
                ProjectRequirement(
                    id="push_notifications",
                    name="Push Notifications",
                    description="Real-time push notifications for messages and activities",
                    category="feature",
                    priority="should_have",
                    estimated_hours=40,
                    dependencies=["real_time_chat"],
                    technologies=["Firebase Cloud Messaging", "React Native Push"]
                ),
                ProjectRequirement(
                    id="media_upload",
                    name="Media Upload & Sharing",
                    description="Photo and video upload with cloud storage",
                    category="feature",
                    priority="could_have",
                    estimated_hours=60,
                    dependencies=["social_features"],
                    technologies=["React Native Image Picker", "Firebase Storage"]
                ),
                ProjectRequirement(
                    id="app_store_deployment",
                    name="App Store Deployment",
                    description="iOS and Android app store submission",
                    category="deployment",
                    priority="must_have",
                    estimated_hours=30,
                    dependencies=["push_notifications"],
                    technologies=["Fastlane", "Expo"]
                )
            ],
            phases=[
                {
                    "name": "Foundation",
                    "duration_weeks": 3,
                    "tasks": ["Project setup", "Authentication", "Basic UI"],
                    "deliverables": ["App skeleton", "User authentication"]
                },
                {
                    "name": "Core Features",
                    "duration_weeks": 6,
                    "tasks": ["Messaging", "Social features", "Real-time updates"],
                    "deliverables": ["Working social app", "Chat functionality"]
                },
                {
                    "name": "Polish & Deploy",
                    "duration_weeks": 3,
                    "tasks": ["Notifications", "Media upload", "App store submission"],
                    "deliverables": ["Published mobile app", "Store presence"]
                }
            ],
            risk_factors=[
                "Platform-specific issues (iOS vs Android)",
                "Real-time performance at scale",
                "App store approval process",
                "Push notification reliability"
            ],
            deliverables=[
                "iOS mobile application",
                "Android mobile application",
                "Backend API service",
                "Real-time chat system",
                "Push notification system",
                "App store listings"
            ],
            success_criteria=[
                "App runs smoothly on both platforms",
                "Real-time messaging works reliably",
                "Users can share content effectively",
                "App is approved by app stores",
                "Push notifications are delivered"
            ],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        templates.append(react_native_app)
        
        # Python Django API Template
        django_api = ProjectTemplate(
            id="django_api_service",
            name="Django REST API Service",
            description="Scalable REST API service with Django and PostgreSQL",
            project_type=ProjectType.API_SERVICE,
            complexity=ProjectComplexity.MEDIUM,
            technology_stack=TechnologyStack.PYTHON_DJANGO,
            estimated_duration_weeks=8,
            team_size_recommended=2,
            requirements=[
                ProjectRequirement(
                    id="api_architecture",
                    name="API Architecture & Models",
                    description="Database models, API endpoints, serializers",
                    category="core",
                    priority="must_have",
                    estimated_hours=80,
                    dependencies=[],
                    technologies=["Django REST Framework", "PostgreSQL"]
                ),
                ProjectRequirement(
                    id="authentication_api",
                    name="Authentication & Authorization",
                    description="JWT authentication, permission system",
                    category="core",
                    priority="must_have",
                    estimated_hours=60,
                    dependencies=["api_architecture"],
                    technologies=["JWT", "Django Auth", "DRF Permissions"]
                ),
                ProjectRequirement(
                    id="api_documentation",
                    name="API Documentation",
                    description="Swagger/OpenAPI documentation",
                    category="feature",
                    priority="should_have",
                    estimated_hours=30,
                    dependencies=["authentication_api"],
                    technologies=["drf-spectacular", "Swagger UI"]
                ),
                ProjectRequirement(
                    id="testing_suite",
                    name="Comprehensive Testing",
                    description="Unit tests, integration tests, API tests",
                    category="feature",
                    priority="should_have",
                    estimated_hours=60,
                    dependencies=["api_documentation"],
                    technologies=["pytest", "Django Test", "Factory Boy"]
                ),
                ProjectRequirement(
                    id="performance_optimization",
                    name="Performance & Caching",
                    description="Database optimization, Redis caching, pagination",
                    category="feature",
                    priority="could_have",
                    estimated_hours=40,
                    dependencies=["testing_suite"],
                    technologies=["Redis", "Django Cache", "Database Indexing"]
                ),
                ProjectRequirement(
                    id="production_deployment",
                    name="Production Deployment",
                    description="Docker containerization, CI/CD, monitoring",
                    category="deployment",
                    priority="must_have",
                    estimated_hours=50,
                    dependencies=["performance_optimization"],
                    technologies=["Docker", "Docker Compose", "Gunicorn", "Nginx"]
                )
            ],
            phases=[
                {
                    "name": "API Foundation",
                    "duration_weeks": 3,
                    "tasks": ["Django setup", "Models", "Basic endpoints"],
                    "deliverables": ["Working API", "Database schema"]
                },
                {
                    "name": "Security & Documentation",
                    "duration_weeks": 3,
                    "tasks": ["Authentication", "Documentation", "Testing"],
                    "deliverables": ["Secure API", "Complete documentation"]
                },
                {
                    "name": "Optimization & Deployment",
                    "duration_weeks": 2,
                    "tasks": ["Performance tuning", "Deployment", "Monitoring"],
                    "deliverables": ["Production API", "Monitoring setup"]
                }
            ],
            risk_factors=[
                "Database performance bottlenecks",
                "Security vulnerabilities in API",
                "Scaling challenges with concurrent users",
                "Third-party service dependencies"
            ],
            deliverables=[
                "Django REST API service",
                "PostgreSQL database",
                "API documentation",
                "Test suite",
                "Docker deployment",
                "CI/CD pipeline"
            ],
            success_criteria=[
                "API handles expected load efficiently",
                "All endpoints are documented and tested",
                "Security audit passes",
                "Deployment pipeline works reliably",
                "Response times under 200ms"
            ],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        templates.append(django_api)
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[ProjectTemplate]:
        """Get a specific template"""
        return self.templates.get(template_id)
    
    def list_templates(self, project_type: Optional[ProjectType] = None,
                      complexity: Optional[ProjectComplexity] = None) -> List[ProjectTemplate]:
        """List templates with optional filtering"""
        templates = list(self.templates.values())
        
        if project_type:
            templates = [t for t in templates if t.project_type == project_type]
        
        if complexity:
            templates = [t for t in templates if t.complexity == complexity]
        
        return sorted(templates, key=lambda x: x.name)
    
    def create_quick_start_wizard(self, template_id: str) -> List[QuickStartWizardStep]:
        """Create quick-start wizard steps for a template"""
        template = self.get_template(template_id)
        if not template:
            return []
        
        wizard_steps = [
            QuickStartWizardStep(
                id="project_basics",
                title="Project Basics",
                description="Define the basic information for your project",
                step_type="input",
                options=[
                    {"field": "project_name", "type": "text", "label": "Project Name", "required": True},
                    {"field": "description", "type": "textarea", "label": "Project Description", "required": False},
                    {"field": "client_name", "type": "text", "label": "Client/Company Name", "required": False},
                    {"field": "target_launch", "type": "date", "label": "Target Launch Date", "required": False}
                ]
            ),
            QuickStartWizardStep(
                id="team_configuration",
                title="Team Configuration",
                description="Configure your team and roles",
                step_type="configuration",
                options=[
                    {"field": "team_size", "type": "number", "label": "Team Size", "default": template.team_size_recommended},
                    {"field": "budget_range", "type": "select", "label": "Budget Range", 
                     "choices": ["<$10k", "$10k-$50k", "$50k-$100k", "$100k+"]},
                    {"field": "hourly_rate", "type": "number", "label": "Average Hourly Rate ($)", "default": 75}
                ]
            ),
            QuickStartWizardStep(
                id="requirements_selection",
                title="Requirements Selection",
                description="Select which features to include in your project",
                step_type="selection",
                options=[
                    {
                        "requirement_id": req.id,
                        "name": req.name,
                        "description": req.description,
                        "hours": req.estimated_hours,
                        "priority": req.priority,
                        "selected": req.priority in ["must_have", "should_have"]
                    }
                    for req in template.requirements
                ]
            ),
            QuickStartWizardStep(
                id="technology_customization",
                title="Technology Stack",
                description="Customize the technology stack for your project",
                step_type="configuration",
                options=[
                    {"field": "frontend_framework", "type": "select", "label": "Frontend Framework",
                     "choices": ["React", "Vue.js", "Angular", "Svelte"], "default": "React"},
                    {"field": "backend_framework", "type": "select", "label": "Backend Framework",
                     "choices": ["Node.js", "Django", "Spring Boot", "Laravel"], "default": "Node.js"},
                    {"field": "database", "type": "select", "label": "Database",
                     "choices": ["PostgreSQL", "MySQL", "MongoDB", "SQLite"], "default": "PostgreSQL"},
                    {"field": "hosting", "type": "select", "label": "Hosting Platform",
                     "choices": ["AWS", "Vercel", "Heroku", "DigitalOcean"], "default": "AWS"}
                ]
            ),
            QuickStartWizardStep(
                id="confirmation",
                title="Project Summary",
                description="Review your project configuration before generating estimate",
                step_type="confirmation"
            )
        ]
        
        return wizard_steps
    
    def generate_estimate_from_wizard(self, template_id: str, wizard_data: Dict[str, Any]) -> ProjectEstimate:
        """Generate project estimate from wizard data"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        project_id = f"project_{int(datetime.now().timestamp())}"
        
        # Calculate total hours based on selected requirements
        selected_requirements = wizard_data.get('requirements_selection', {})
        total_hours = 0
        selected_reqs = []
        
        for req in template.requirements:
            if selected_requirements.get(req.id, req.priority in ["must_have", "should_have"]):
                total_hours += req.estimated_hours
                selected_reqs.append(req)
        
        # Apply complexity multiplier
        complexity_multipliers = {
            ProjectComplexity.SIMPLE: 0.8,
            ProjectComplexity.MEDIUM: 1.0,
            ProjectComplexity.COMPLEX: 1.3,
            ProjectComplexity.ENTERPRISE: 1.6
        }
        total_hours *= complexity_multipliers.get(template.complexity, 1.0)
        
        # Calculate cost
        hourly_rate = wizard_data.get('team_configuration', {}).get('hourly_rate', 75)
        total_cost = total_hours * hourly_rate
        
        # Calculate duration
        team_size = wizard_data.get('team_configuration', {}).get('team_size', template.team_size_recommended)
        duration_weeks = (total_hours / (team_size * 40))  # 40 hours per week per person
        
        # Generate team composition
        team_composition = self._generate_team_composition(template, team_size, selected_reqs)
        
        # Generate phase breakdown
        phase_breakdown = self._generate_phase_breakdown(template, total_hours, duration_weeks)
        
        # Risk assessment
        risk_assessment = self._generate_risk_assessment(template, wizard_data)
        
        # Recommendations
        recommendations = self._generate_recommendations(template, wizard_data, total_hours)
        
        return ProjectEstimate(
            project_id=project_id,
            template_id=template_id,
            total_hours=total_hours,
            total_cost=total_cost,
            duration_weeks=duration_weeks,
            team_composition=team_composition,
            phase_breakdown=phase_breakdown,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            generated_at=datetime.now()
        )
    
    def _generate_team_composition(self, template: ProjectTemplate, team_size: int, 
                                 requirements: List[ProjectRequirement]) -> Dict[str, int]:
        """Generate recommended team composition"""
        # Analyze requirements to determine needed roles
        roles_needed = set()
        
        for req in requirements:
            # Simple role mapping based on technologies and categories
            if any(tech in ['React', 'Vue', 'Angular'] for tech in req.technologies):
                roles_needed.add('Frontend Developer')
            if any(tech in ['Node.js', 'Django', 'Spring Boot'] for tech in req.technologies):
                roles_needed.add('Backend Developer')
            if req.category == 'deployment':
                roles_needed.add('DevOps Engineer')
            if 'UI' in req.description or 'design' in req.description.lower():
                roles_needed.add('UI/UX Designer')
        
        # Default composition based on project type
        if template.project_type == ProjectType.WEB_APPLICATION:
            base_composition = {
                'Frontend Developer': max(1, team_size // 3),
                'Backend Developer': max(1, team_size // 3),
                'Full-stack Developer': max(1, team_size - (2 * (team_size // 3))),
                'UI/UX Designer': 1 if team_size > 2 else 0,
                'DevOps Engineer': 1 if team_size > 3 else 0
            }
        elif template.project_type == ProjectType.MOBILE_APP:
            base_composition = {
                'Mobile Developer': max(1, team_size // 2),
                'Backend Developer': max(1, team_size // 3),
                'UI/UX Designer': 1 if team_size > 2 else 0,
                'QA Engineer': 1 if team_size > 3 else 0
            }
        else:
            base_composition = {
                'Full-stack Developer': max(1, team_size // 2),
                'Senior Developer': max(1, team_size // 3),
                'UI/UX Designer': 1 if team_size > 2 else 0
            }
        
        # Ensure total doesn't exceed team size
        total_assigned = sum(base_composition.values())
        if total_assigned > team_size:
            # Reduce proportionally
            factor = team_size / total_assigned
            base_composition = {role: max(1, int(count * factor)) 
                             for role, count in base_composition.items() if count > 0}
        
        return base_composition
    
    def _generate_phase_breakdown(self, template: ProjectTemplate, total_hours: float, 
                                duration_weeks: float) -> List[Dict[str, Any]]:
        """Generate phase breakdown with hours and timeline"""
        phase_breakdown = []
        
        for i, phase in enumerate(template.phases):
            phase_duration = phase.get('duration_weeks', duration_weeks / len(template.phases))
            phase_hours = (phase_duration / duration_weeks) * total_hours
            
            phase_breakdown.append({
                'name': phase['name'],
                'duration_weeks': phase_duration,
                'estimated_hours': phase_hours,
                'tasks': phase.get('tasks', []),
                'deliverables': phase.get('deliverables', []),
                'start_week': sum(p['duration_weeks'] for p in template.phases[:i]) + 1,
                'end_week': sum(p['duration_weeks'] for p in template.phases[:i+1])
            })
        
        return phase_breakdown
    
    def _generate_risk_assessment(self, template: ProjectTemplate, 
                                wizard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate risk assessment for the project"""
        risks = []
        
        # Add template-specific risks
        for risk in template.risk_factors:
            risks.append({
                'description': risk,
                'probability': 'medium',
                'impact': 'medium',
                'mitigation': 'Regular monitoring and proactive management'
            })
        
        # Add risks based on wizard data
        team_size = wizard_data.get('team_configuration', {}).get('team_size', 1)
        if team_size < template.team_size_recommended:
            risks.append({
                'description': 'Team size smaller than recommended',
                'probability': 'high',
                'impact': 'medium',
                'mitigation': 'Consider extending timeline or adding team members'
            })
        
        budget_range = wizard_data.get('team_configuration', {}).get('budget_range', '')
        if budget_range in ['<$10k', '$10k-$50k'] and template.complexity in [ProjectComplexity.COMPLEX, ProjectComplexity.ENTERPRISE]:
            risks.append({
                'description': 'Budget may be insufficient for project complexity',
                'probability': 'medium',
                'impact': 'high',
                'mitigation': 'Prioritize core features and plan phased delivery'
            })
        
        return {
            'overall_risk_level': self._calculate_overall_risk(risks),
            'risks': risks,
            'risk_count': len(risks)
        }
    
    def _calculate_overall_risk(self, risks: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level"""
        high_risks = sum(1 for r in risks if r['probability'] == 'high' or r['impact'] == 'high')
        
        if high_risks >= 3:
            return 'high'
        elif high_risks >= 1:
            return 'medium'
        else:
            return 'low'
    
    def _generate_recommendations(self, template: ProjectTemplate, wizard_data: Dict[str, Any], 
                                total_hours: float) -> List[str]:
        """Generate project recommendations"""
        recommendations = []
        
        # Timeline recommendations
        if total_hours > 800:
            recommendations.append("Consider breaking the project into phases for better risk management")
        
        # Team recommendations
        team_size = wizard_data.get('team_configuration', {}).get('team_size', 1)
        if team_size < template.team_size_recommended:
            recommendations.append(f"Consider increasing team size to {template.team_size_recommended} for optimal delivery")
        
        # Technology recommendations
        if template.technology_stack == TechnologyStack.REACT_NODE:
            recommendations.append("Use TypeScript for better code maintainability")
            recommendations.append("Implement proper testing strategy with Jest and React Testing Library")
        
        # Budget recommendations
        budget_range = wizard_data.get('team_configuration', {}).get('budget_range', '')
        if budget_range in ['<$10k', '$10k-$50k']:
            recommendations.append("Focus on MVP features first to validate concept within budget")
        
        # Complexity-specific recommendations
        if template.complexity == ProjectComplexity.ENTERPRISE:
            recommendations.append("Implement proper CI/CD pipeline from the start")
            recommendations.append("Plan for scalability and performance testing")
            recommendations.append("Consider microservices architecture for better maintainability")
        
        return recommendations
    
    def add_custom_template(self, template: ProjectTemplate):
        """Add a custom project template"""
        self.templates[template.id] = template
        self.save_templates()
    
    def update_template(self, template_id: str, **kwargs):
        """Update an existing template"""
        if template_id in self.templates:
            template = self.templates[template_id]
            for key, value in kwargs.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            template.updated_at = datetime.now()
            self.save_templates()
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a template"""
        if template_id in self.templates:
            del self.templates[template_id]
            self.save_templates()
            return True
        return False
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """Get statistics about templates"""
        stats = {
            'total_templates': len(self.templates),
            'by_type': {},
            'by_complexity': {},
            'by_technology': {},
            'average_duration_weeks': 0,
            'average_team_size': 0
        }
        
        if not self.templates:
            return stats
        
        # Count by type
        for template in self.templates.values():
            proj_type = template.project_type.value
            stats['by_type'][proj_type] = stats['by_type'].get(proj_type, 0) + 1
            
            complexity = template.complexity.value
            stats['by_complexity'][complexity] = stats['by_complexity'].get(complexity, 0) + 1
            
            tech_stack = template.technology_stack.value
            stats['by_technology'][tech_stack] = stats['by_technology'].get(tech_stack, 0) + 1
        
        # Calculate averages
        stats['average_duration_weeks'] = sum(t.estimated_duration_weeks for t in self.templates.values()) / len(self.templates)
        stats['average_team_size'] = sum(t.team_size_recommended for t in self.templates.values()) / len(self.templates)
        
        return stats

# Global template manager instance
template_manager = ProjectTemplateManager()