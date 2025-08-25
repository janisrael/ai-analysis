import os
import json
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import statistics
from collections import defaultdict, Counter
import math

class ProjectRequirement:
    """Represents a single project requirement"""
    
    def __init__(self, requirement_text: str, complexity: float = 0.5, priority: int = 3):
        self.text = requirement_text
        self.complexity = complexity  # 0.0 to 1.0
        self.priority = priority  # 1-5, 1 being highest
        self.estimated_hours = 0
        self.required_skills = []
        self.risk_factors = []

class ProjectEstimate:
    """Contains comprehensive project estimation results"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.total_hours = 0
        self.complexity_score = 0.5  # 0.0 to 1.0
        self.difficulty_level = "Medium"  # Easy, Medium, Hard, Expert
        self.confidence_level = 0.8  # 0.0 to 1.0
        
        # Time estimates
        self.optimistic_hours = 0
        self.realistic_hours = 0
        self.pessimistic_hours = 0
        
        # Team recommendations
        self.recommended_team_size = 1
        self.recommended_roles = []
        self.team_members = []
        
        # Risk analysis
        self.risk_factors = []
        self.risk_score = 0.3  # 0.0 to 1.0
        
        # Technology analysis
        self.technologies = []
        self.tech_complexity = {}
        
        # Breakdown
        self.phase_breakdown = {}
        self.skill_breakdown = {}
        
        # Similar projects
        self.similar_projects = []
        
        # Generated at
        self.created_at = datetime.now()

class ProjectEstimator:
    """AI-powered project estimation and team recommendation engine"""
    
    def __init__(self, data_source_manager):
        self.data_manager = data_source_manager
        self.logger = logging.getLogger(__name__)
        
        # Load estimation knowledge base
        self.knowledge_base = self.load_knowledge_base()
        
        # Technology complexity mappings
        self.tech_complexity = {
            # Web Technologies
            "html": 0.1, "css": 0.2, "javascript": 0.4, "react": 0.6, "vue": 0.5, "angular": 0.7,
            "node.js": 0.5, "express": 0.4, "django": 0.6, "flask": 0.4, "fastapi": 0.5,
            "wordpress": 0.3, "webflow": 0.2, "shopify": 0.3, "squarespace": 0.2,
            
            # Mobile Technologies
            "ios": 0.7, "android": 0.7, "react native": 0.6, "flutter": 0.6, "ionic": 0.5,
            "swift": 0.7, "kotlin": 0.7, "java": 0.6, "objective-c": 0.8,
            
            # Backend Technologies
            "python": 0.5, "java": 0.6, "c#": 0.6, "php": 0.4, "ruby": 0.5, "go": 0.7,
            "mysql": 0.4, "postgresql": 0.5, "mongodb": 0.5, "redis": 0.4,
            "docker": 0.6, "kubernetes": 0.8, "aws": 0.7, "azure": 0.7, "gcp": 0.7,
            
            # AI/ML Technologies
            "machine learning": 0.8, "deep learning": 0.9, "tensorflow": 0.8, "pytorch": 0.8,
            "nlp": 0.8, "computer vision": 0.9, "data science": 0.7,
            
            # Design Technologies
            "figma": 0.3, "sketch": 0.3, "adobe xd": 0.4, "photoshop": 0.4, "illustrator": 0.5,
            "ui/ux": 0.5, "graphic design": 0.4, "branding": 0.5,
            
            # Other
            "api integration": 0.5, "payment integration": 0.6, "authentication": 0.5,
            "real-time": 0.7, "blockchain": 0.9, "game development": 0.8
        }
        
        # Skill categories and their base complexities
        self.skill_categories = {
            "frontend": ["html", "css", "javascript", "react", "vue", "angular", "ui/ux"],
            "backend": ["python", "java", "node.js", "django", "flask", "mysql", "postgresql"],
            "mobile": ["ios", "android", "react native", "flutter", "swift", "kotlin"],
            "devops": ["docker", "kubernetes", "aws", "azure", "gcp", "ci/cd"],
            "design": ["figma", "sketch", "ui/ux", "graphic design", "branding"],
            "ai/ml": ["machine learning", "deep learning", "tensorflow", "pytorch", "data science"],
            "cms": ["wordpress", "webflow", "shopify", "drupal"]
        }
        
        # Risk factors and their impact
        self.risk_factors = {
            "new_technology": {"impact": 0.3, "description": "Using unfamiliar technology"},
            "tight_deadline": {"impact": 0.4, "description": "Very short timeline"},
            "complex_integration": {"impact": 0.5, "description": "Multiple system integrations"},
            "unclear_requirements": {"impact": 0.6, "description": "Ambiguous or changing requirements"},
            "large_team": {"impact": 0.2, "description": "Coordination overhead with large team"},
            "remote_team": {"impact": 0.1, "description": "Distributed team communication"},
            "first_time_client": {"impact": 0.2, "description": "New client relationship"},
            "experimental_features": {"impact": 0.7, "description": "Unproven or experimental functionality"},
            "performance_critical": {"impact": 0.4, "description": "High performance requirements"},
            "security_sensitive": {"impact": 0.5, "description": "High security requirements"}
        }
    
    def load_knowledge_base(self) -> Dict:
        """Load project estimation knowledge base"""
        knowledge_file = "data/estimation_knowledge.json"
        
        if os.path.exists(knowledge_file):
            try:
                with open(knowledge_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load knowledge base: {e}")
        
        # Create default knowledge base
        default_kb = {
            "project_types": {
                "website": {
                    "base_hours": 40,
                    "complexity_multiplier": 1.0,
                    "common_features": ["responsive design", "contact form", "cms", "seo"],
                    "typical_roles": ["frontend developer", "designer", "content creator"]
                },
                "web_app": {
                    "base_hours": 120,
                    "complexity_multiplier": 1.5,
                    "common_features": ["user authentication", "database", "api", "admin panel"],
                    "typical_roles": ["frontend developer", "backend developer", "ui/ux designer", "project manager"]
                },
                "mobile_app": {
                    "base_hours": 200,
                    "complexity_multiplier": 1.8,
                    "common_features": ["native ui", "api integration", "offline mode", "push notifications"],
                    "typical_roles": ["mobile developer", "backend developer", "ui/ux designer", "qa tester"]
                },
                "e-commerce": {
                    "base_hours": 160,
                    "complexity_multiplier": 1.6,
                    "common_features": ["product catalog", "shopping cart", "payment processing", "order management"],
                    "typical_roles": ["frontend developer", "backend developer", "ui/ux designer", "payment specialist"]
                }
            },
            "feature_estimates": {
                "user_authentication": 16,
                "payment_integration": 24,
                "api_integration": 12,
                "admin_panel": 32,
                "responsive_design": 20,
                "search_functionality": 16,
                "real_time_features": 40,
                "file_upload": 8,
                "email_notifications": 12,
                "social_login": 8,
                "multi_language": 24,
                "reporting_dashboard": 40
            },
            "technology_learning_curves": {
                "react": 0.8,
                "vue": 0.6,
                "angular": 1.0,
                "django": 0.7,
                "flask": 0.5,
                "wordpress": 0.3,
                "webflow": 0.2
            }
        }
        
        # Save default knowledge base
        os.makedirs(os.path.dirname(knowledge_file), exist_ok=True)
        with open(knowledge_file, 'w') as f:
            json.dump(default_kb, f, indent=2)
        
        return default_kb
    
    def estimate_project(self, project_description: str, requirements: List[str] = None, 
                        technologies: List[str] = None, deadline: str = None) -> ProjectEstimate:
        """Generate comprehensive project estimate"""
        
        # Create estimate object
        estimate = ProjectEstimate(self.extract_project_name(project_description))
        
        # Analyze project description
        project_analysis = self.analyze_project_description(project_description)
        estimate.technologies = technologies or project_analysis.get("technologies", [])
        
        # Parse requirements
        parsed_requirements = self.parse_requirements(requirements or [])
        
        # Determine project type and complexity
        project_type = self.determine_project_type(project_description, estimate.technologies)
        complexity_factors = self.analyze_complexity(project_description, parsed_requirements, estimate.technologies)
        
        estimate.complexity_score = complexity_factors["overall_complexity"]
        estimate.difficulty_level = self.get_difficulty_level(estimate.complexity_score)
        
        # Calculate time estimates
        base_hours = self.calculate_base_hours(project_type, parsed_requirements)
        complexity_multiplier = 1 + (estimate.complexity_score - 0.5)
        
        estimate.realistic_hours = int(base_hours * complexity_multiplier)
        estimate.optimistic_hours = int(estimate.realistic_hours * 0.8)
        estimate.pessimistic_hours = int(estimate.realistic_hours * 1.5)
        estimate.total_hours = estimate.realistic_hours
        
        # Analyze risks
        estimate.risk_factors = self.identify_risk_factors(
            project_description, parsed_requirements, estimate.technologies, deadline
        )
        estimate.risk_score = self.calculate_risk_score(estimate.risk_factors)
        
        # Adjust estimates based on risk
        if estimate.risk_score > 0.6:
            estimate.total_hours = int(estimate.total_hours * 1.3)
            estimate.realistic_hours = estimate.total_hours
        
        # Generate team recommendations
        estimate.recommended_roles = self.recommend_roles(project_type, estimate.technologies, estimate.complexity_score)
        estimate.team_members = self.recommend_team_members(estimate.recommended_roles, estimate.technologies)
        estimate.recommended_team_size = len(estimate.recommended_roles)
        
        # Create breakdowns
        estimate.phase_breakdown = self.create_phase_breakdown(project_type, estimate.total_hours)
        estimate.skill_breakdown = self.create_skill_breakdown(estimate.technologies, estimate.total_hours)
        
        # Find similar projects
        estimate.similar_projects = self.find_similar_projects(project_description, estimate.technologies)
        
        # Calculate confidence
        estimate.confidence_level = self.calculate_confidence(estimate)
        
        # Technology complexity analysis
        estimate.tech_complexity = self.analyze_tech_complexity(estimate.technologies)
        
        return estimate
    
    def extract_project_name(self, description: str) -> str:
        """Extract project name from description"""
        # Look for explicit project names
        patterns = [
            r"project[:\s]+([^,\n\.]+)",
            r"build[ing]*\s+(?:a\s+)?([^,\n\.]+)",
            r"create[ing]*\s+(?:a\s+)?([^,\n\.]+)",
            r"develop[ing]*\s+(?:a\s+)?([^,\n\.]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description.lower())
            if match:
                name = match.group(1).strip()
                if len(name) > 3 and len(name) < 50:
                    return name.title()
        
        # Fallback: use first few words
        words = description.split()[:4]
        return " ".join(words).title()
    
    def analyze_project_description(self, description: str) -> Dict:
        """Analyze project description to extract key information"""
        analysis = {
            "technologies": [],
            "features": [],
            "complexity_indicators": [],
            "project_type": None
        }
        
        description_lower = description.lower()
        
        # Extract technologies
        for tech, _ in self.tech_complexity.items():
            if tech in description_lower:
                analysis["technologies"].append(tech)
        
        # Identify project type
        if any(word in description_lower for word in ["website", "site", "landing page"]):
            analysis["project_type"] = "website"
        elif any(word in description_lower for word in ["web app", "web application", "dashboard"]):
            analysis["project_type"] = "web_app"
        elif any(word in description_lower for word in ["mobile app", "ios app", "android app"]):
            analysis["project_type"] = "mobile_app"
        elif any(word in description_lower for word in ["e-commerce", "online store", "shop"]):
            analysis["project_type"] = "e-commerce"
        
        # Extract features
        feature_keywords = {
            "user_authentication": ["login", "signup", "authentication", "user accounts"],
            "payment_integration": ["payment", "checkout", "stripe", "paypal", "billing"],
            "api_integration": ["api", "integration", "third-party", "external service"],
            "admin_panel": ["admin", "dashboard", "management", "control panel"],
            "real_time": ["real-time", "live", "chat", "notifications"],
            "search": ["search", "filter", "find"],
            "file_upload": ["upload", "file", "image", "document"],
            "responsive": ["responsive", "mobile-friendly", "adaptive"],
            "multi_language": ["multi-language", "internationalization", "i18n"]
        }
        
        for feature, keywords in feature_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                analysis["features"].append(feature)
        
        # Complexity indicators
        complexity_indicators = [
            "complex", "advanced", "sophisticated", "enterprise", "scalable",
            "high-performance", "real-time", "machine learning", "ai",
            "blockchain", "microservices", "distributed"
        ]
        
        for indicator in complexity_indicators:
            if indicator in description_lower:
                analysis["complexity_indicators"].append(indicator)
        
        return analysis
    
    def parse_requirements(self, requirements: List[str]) -> List[ProjectRequirement]:
        """Parse and analyze project requirements"""
        parsed_requirements = []
        
        for req_text in requirements:
            requirement = ProjectRequirement(req_text)
            
            # Analyze complexity
            requirement.complexity = self.estimate_requirement_complexity(req_text)
            
            # Extract required skills
            requirement.required_skills = self.extract_required_skills(req_text)
            
            # Identify risk factors
            requirement.risk_factors = self.identify_requirement_risks(req_text)
            
            # Estimate hours for this requirement
            requirement.estimated_hours = self.estimate_requirement_hours(req_text, requirement.complexity)
            
            parsed_requirements.append(requirement)
        
        return parsed_requirements
    
    def estimate_requirement_complexity(self, requirement: str) -> float:
        """Estimate complexity of a single requirement (0.0 to 1.0)"""
        req_lower = requirement.lower()
        complexity = 0.5  # Base complexity
        
        # High complexity keywords
        high_complexity = ["complex", "advanced", "sophisticated", "real-time", "ai", "machine learning", "custom"]
        low_complexity = ["simple", "basic", "standard", "typical", "normal"]
        
        for keyword in high_complexity:
            if keyword in req_lower:
                complexity += 0.15
        
        for keyword in low_complexity:
            if keyword in req_lower:
                complexity -= 0.15
        
        # Technology-based complexity
        for tech, tech_complexity in self.tech_complexity.items():
            if tech in req_lower:
                complexity += (tech_complexity - 0.5) * 0.3
        
        return max(0.0, min(1.0, complexity))
    
    def extract_required_skills(self, requirement: str) -> List[str]:
        """Extract required skills from requirement text"""
        req_lower = requirement.lower()
        required_skills = []
        
        # Check for technology mentions
        for tech in self.tech_complexity.keys():
            if tech in req_lower:
                required_skills.append(tech)
        
        # Check for skill categories
        skill_keywords = {
            "frontend": ["frontend", "front-end", "ui", "interface", "client-side"],
            "backend": ["backend", "back-end", "server", "database", "api"],
            "design": ["design", "ui/ux", "visual", "graphics", "branding"],
            "mobile": ["mobile", "ios", "android", "app"],
            "devops": ["deployment", "hosting", "server", "cloud", "devops"]
        }
        
        for skill, keywords in skill_keywords.items():
            if any(keyword in req_lower for keyword in keywords):
                required_skills.append(skill)
        
        return list(set(required_skills))  # Remove duplicates
    
    def identify_requirement_risks(self, requirement: str) -> List[str]:
        """Identify risk factors in a requirement"""
        req_lower = requirement.lower()
        risks = []
        
        risk_keywords = {
            "unclear_requirements": ["maybe", "possibly", "might", "unclear", "tbd", "to be determined"],
            "new_technology": ["new", "latest", "cutting-edge", "experimental"],
            "complex_integration": ["integrate", "third-party", "external", "api"],
            "performance_critical": ["fast", "performance", "speed", "optimize", "scalable"],
            "security_sensitive": ["secure", "security", "authentication", "authorization", "encryption"]
        }
        
        for risk, keywords in risk_keywords.items():
            if any(keyword in req_lower for keyword in keywords):
                risks.append(risk)
        
        return risks
    
    def estimate_requirement_hours(self, requirement: str, complexity: float) -> int:
        """Estimate hours for a single requirement"""
        base_hours = 8  # Base hours per requirement
        
        # Adjust based on complexity
        complexity_multiplier = 0.5 + (complexity * 1.5)
        
        # Check for specific features
        feature_hours = self.knowledge_base.get("feature_estimates", {})
        req_lower = requirement.lower()
        
        for feature, hours in feature_hours.items():
            if feature.replace("_", " ") in req_lower:
                return int(hours * complexity_multiplier)
        
        return int(base_hours * complexity_multiplier)
    
    def determine_project_type(self, description: str, technologies: List[str]) -> str:
        """Determine the type of project"""
        desc_lower = description.lower()
        
        # Check explicit mentions
        type_keywords = {
            "website": ["website", "site", "landing page", "portfolio", "blog"],
            "web_app": ["web app", "web application", "dashboard", "platform", "system"],
            "mobile_app": ["mobile app", "ios app", "android app", "mobile application"],
            "e-commerce": ["e-commerce", "online store", "shop", "marketplace", "store"]
        }
        
        for project_type, keywords in type_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                return project_type
        
        # Infer from technologies
        if any(tech in technologies for tech in ["ios", "android", "react native", "flutter"]):
            return "mobile_app"
        elif any(tech in technologies for tech in ["shopify", "woocommerce", "magento"]):
            return "e-commerce"
        elif any(tech in technologies for tech in ["react", "vue", "angular", "django", "flask"]):
            return "web_app"
        else:
            return "website"  # Default
    
    def analyze_complexity(self, description: str, requirements: List[ProjectRequirement], 
                          technologies: List[str]) -> Dict:
        """Analyze overall project complexity"""
        factors = {
            "technology_complexity": 0.5,
            "requirement_complexity": 0.5,
            "integration_complexity": 0.5,
            "overall_complexity": 0.5
        }
        
        # Technology complexity
        if technologies:
            tech_complexities = [self.tech_complexity.get(tech, 0.5) for tech in technologies]
            factors["technology_complexity"] = statistics.mean(tech_complexities)
        
        # Requirement complexity
        if requirements:
            req_complexities = [req.complexity for req in requirements]
            factors["requirement_complexity"] = statistics.mean(req_complexities)
        
        # Integration complexity (based on number of technologies and integrations)
        integration_indicators = len(technologies) + description.lower().count("integration") * 2
        factors["integration_complexity"] = min(1.0, integration_indicators / 10)
        
        # Overall complexity (weighted average)
        factors["overall_complexity"] = (
            factors["technology_complexity"] * 0.4 +
            factors["requirement_complexity"] * 0.4 +
            factors["integration_complexity"] * 0.2
        )
        
        return factors
    
    def calculate_base_hours(self, project_type: str, requirements: List[ProjectRequirement]) -> int:
        """Calculate base hours for the project"""
        project_types = self.knowledge_base.get("project_types", {})
        
        if project_type in project_types:
            base_hours = project_types[project_type]["base_hours"]
        else:
            base_hours = 80  # Default
        
        # Add hours for specific requirements
        requirement_hours = sum(req.estimated_hours for req in requirements)
        
        return base_hours + requirement_hours
    
    def identify_risk_factors(self, description: str, requirements: List[ProjectRequirement], 
                             technologies: List[str], deadline: str = None) -> List[Dict]:
        """Identify project risk factors"""
        risks = []
        desc_lower = description.lower()
        
        # Technology risks
        new_tech_count = sum(1 for tech in technologies if self.tech_complexity.get(tech, 0.5) > 0.7)
        if new_tech_count > 2:
            risks.append({
                "type": "new_technology",
                "description": f"Using {new_tech_count} complex technologies",
                "impact": self.risk_factors["new_technology"]["impact"]
            })
        
        # Requirements risks
        unclear_requirements = sum(1 for req in requirements if "unclear_requirements" in req.risk_factors)
        if unclear_requirements > 0:
            risks.append({
                "type": "unclear_requirements",
                "description": f"{unclear_requirements} unclear requirements identified",
                "impact": self.risk_factors["unclear_requirements"]["impact"]
            })
        
        # Complexity risks
        if any(keyword in desc_lower for keyword in ["complex", "sophisticated", "advanced"]):
            risks.append({
                "type": "experimental_features",
                "description": "Complex or advanced features required",
                "impact": self.risk_factors["experimental_features"]["impact"]
            })
        
        # Integration risks
        integration_count = desc_lower.count("integration") + desc_lower.count("api")
        if integration_count > 2:
            risks.append({
                "type": "complex_integration",
                "description": f"Multiple integrations required ({integration_count})",
                "impact": self.risk_factors["complex_integration"]["impact"]
            })
        
        # Timeline risks
        if deadline:
            try:
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                days_available = (deadline_date - datetime.now()).days
                if days_available < 30:
                    risks.append({
                        "type": "tight_deadline",
                        "description": f"Only {days_available} days available",
                        "impact": self.risk_factors["tight_deadline"]["impact"]
                    })
            except:
                pass
        
        return risks
    
    def calculate_risk_score(self, risk_factors: List[Dict]) -> float:
        """Calculate overall risk score (0.0 to 1.0)"""
        if not risk_factors:
            return 0.2  # Baseline risk
        
        # Calculate weighted risk
        total_impact = sum(risk["impact"] for risk in risk_factors)
        risk_count = len(risk_factors)
        
        # Normalize and cap at 1.0
        risk_score = min(1.0, total_impact / max(risk_count, 1))
        
        return risk_score
    
    def recommend_roles(self, project_type: str, technologies: List[str], complexity: float) -> List[str]:
        """Recommend team roles for the project"""
        roles = []
        
        # Base roles by project type
        project_types = self.knowledge_base.get("project_types", {})
        if project_type in project_types:
            roles.extend(project_types[project_type]["typical_roles"])
        
        # Technology-specific roles
        tech_roles = {
            "react": "frontend developer",
            "vue": "frontend developer", 
            "angular": "frontend developer",
            "django": "backend developer",
            "flask": "backend developer",
            "node.js": "backend developer",
            "ios": "ios developer",
            "android": "android developer",
            "react native": "mobile developer",
            "flutter": "mobile developer",
            "figma": "ui/ux designer",
            "sketch": "ui/ux designer",
            "aws": "devops engineer",
            "docker": "devops engineer",
            "machine learning": "data scientist"
        }
        
        for tech in technologies:
            if tech in tech_roles and tech_roles[tech] not in roles:
                roles.append(tech_roles[tech])
        
        # Add roles based on complexity
        if complexity > 0.7:
            if "project manager" not in roles:
                roles.append("project manager")
            if "qa tester" not in roles:
                roles.append("qa tester")
        
        if complexity > 0.8:
            if "tech lead" not in roles:
                roles.append("tech lead")
        
        return list(set(roles))  # Remove duplicates
    
    def recommend_team_members(self, roles: List[str], technologies: List[str]) -> List[Dict]:
        """Recommend specific team members based on skills and availability"""
        team_members = self.data_manager.get_team_members()
        recommendations = []
        
        for role in roles:
            # Find team members with matching skills
            candidates = []
            
            for member in team_members:
                member_skills = member.get("skills", [])
                if isinstance(member_skills, str):
                    member_skills = [member_skills]
                
                # Calculate skill match score
                skill_match = self.calculate_skill_match(member_skills, technologies, role)
                
                if skill_match > 0.3:  # Minimum threshold
                    candidates.append({
                        "member": member,
                        "skill_match": skill_match,
                        "role": role
                    })
            
            # Sort by skill match and take top candidates
            candidates.sort(key=lambda x: x["skill_match"], reverse=True)
            
            if candidates:
                best_candidate = candidates[0]
                recommendations.append({
                    "name": best_candidate["member"].get("name", "Unknown"),
                    "role": role,
                    "skill_match": best_candidate["skill_match"],
                    "skills": best_candidate["member"].get("skills", []),
                    "hourly_rate": best_candidate["member"].get("hourly_rate", 0),
                    "availability": best_candidate["member"].get("availability", "unknown"),
                    "experience": best_candidate["member"].get("experience", "unknown")
                })
            else:
                # No suitable team member found
                recommendations.append({
                    "name": f"[Hire {role.title()}]",
                    "role": role,
                    "skill_match": 0.0,
                    "skills": technologies,
                    "hourly_rate": self.estimate_hourly_rate(role),
                    "availability": "to_be_hired",
                    "experience": "required"
                })
        
        return recommendations
    
    def calculate_skill_match(self, member_skills: List[str], technologies: List[str], role: str) -> float:
        """Calculate how well a team member's skills match the project needs"""
        if not member_skills:
            return 0.0
        
        member_skills_lower = [skill.lower() for skill in member_skills]
        technologies_lower = [tech.lower() for tech in technologies]
        
        # Direct technology matches
        tech_matches = sum(1 for tech in technologies_lower if tech in member_skills_lower)
        tech_score = tech_matches / max(len(technologies), 1)
        
        # Role-based matches
        role_keywords = {
            "frontend developer": ["frontend", "react", "vue", "angular", "javascript", "html", "css"],
            "backend developer": ["backend", "python", "java", "node.js", "api", "database"],
            "ui/ux designer": ["ui", "ux", "design", "figma", "sketch", "user experience"],
            "mobile developer": ["mobile", "ios", "android", "react native", "flutter"],
            "devops engineer": ["devops", "aws", "docker", "kubernetes", "ci/cd"],
            "project manager": ["project management", "scrum", "agile", "planning"],
            "qa tester": ["testing", "qa", "quality assurance", "automation"]
        }
        
        role_score = 0.0
        if role in role_keywords:
            role_matches = sum(1 for keyword in role_keywords[role] 
                             if any(keyword in skill for skill in member_skills_lower))
            role_score = role_matches / len(role_keywords[role])
        
        # Combined score
        return (tech_score * 0.6) + (role_score * 0.4)
    
    def estimate_hourly_rate(self, role: str) -> int:
        """Estimate hourly rate for a role"""
        role_rates = {
            "frontend developer": 75,
            "backend developer": 85,
            "ui/ux designer": 70,
            "mobile developer": 90,
            "devops engineer": 95,
            "project manager": 80,
            "qa tester": 60,
            "tech lead": 120,
            "data scientist": 100
        }
        
        return role_rates.get(role, 75)
    
    def create_phase_breakdown(self, project_type: str, total_hours: int) -> Dict:
        """Create project phase breakdown"""
        phase_templates = {
            "website": {
                "planning": 0.15,
                "design": 0.25,
                "development": 0.45,
                "testing": 0.10,
                "deployment": 0.05
            },
            "web_app": {
                "planning": 0.20,
                "design": 0.20,
                "development": 0.40,
                "testing": 0.15,
                "deployment": 0.05
            },
            "mobile_app": {
                "planning": 0.15,
                "design": 0.20,
                "development": 0.45,
                "testing": 0.15,
                "deployment": 0.05
            },
            "e-commerce": {
                "planning": 0.20,
                "design": 0.20,
                "development": 0.35,
                "testing": 0.20,
                "deployment": 0.05
            }
        }
        
        template = phase_templates.get(project_type, phase_templates["website"])
        breakdown = {}
        
        for phase, percentage in template.items():
            breakdown[phase] = {
                "hours": int(total_hours * percentage),
                "percentage": percentage * 100,
                "description": self.get_phase_description(phase)
            }
        
        return breakdown
    
    def get_phase_description(self, phase: str) -> str:
        """Get description for a project phase"""
        descriptions = {
            "planning": "Requirements analysis, architecture planning, and project setup",
            "design": "UI/UX design, wireframes, mockups, and design system creation",
            "development": "Core development, feature implementation, and integration",
            "testing": "Quality assurance, bug fixes, and performance optimization",
            "deployment": "Production deployment, setup, and go-live activities"
        }
        
        return descriptions.get(phase, "Project phase")
    
    def create_skill_breakdown(self, technologies: List[str], total_hours: int) -> Dict:
        """Create skill-based hour breakdown"""
        if not technologies:
            return {}
        
        # Group technologies by skill category
        skill_groups = defaultdict(list)
        
        for tech in technologies:
            for category, techs in self.skill_categories.items():
                if tech in techs:
                    skill_groups[category].append(tech)
                    break
            else:
                skill_groups["other"].append(tech)
        
        # Distribute hours based on complexity and skill group
        breakdown = {}
        total_complexity = sum(self.tech_complexity.get(tech, 0.5) for tech in technologies)
        
        for category, techs in skill_groups.items():
            category_complexity = sum(self.tech_complexity.get(tech, 0.5) for tech in techs)
            percentage = category_complexity / max(total_complexity, 1)
            
            breakdown[category] = {
                "hours": int(total_hours * percentage),
                "percentage": percentage * 100,
                "technologies": techs
            }
        
        return breakdown
    
    def find_similar_projects(self, description: str, technologies: List[str]) -> List[Dict]:
        """Find similar projects from historical data"""
        all_projects = self.data_manager.get_all_projects()
        similar_projects = []
        
        desc_words = set(description.lower().split())
        
        for project in all_projects:
            # Calculate similarity score
            similarity_score = self.calculate_project_similarity(
                description, technologies, project
            )
            
            if similarity_score > 0.3:  # Minimum similarity threshold
                similar_projects.append({
                    "project": project,
                    "similarity": similarity_score,
                    "name": project.get("project_name", project.get("name", "Unknown Project")),
                    "estimated_hours": project.get("estimated_hours", 0),
                    "actual_hours": project.get("actual_hours", 0),
                    "status": project.get("status", "unknown")
                })
        
        # Sort by similarity and return top matches
        similar_projects.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_projects[:5]
    
    def calculate_project_similarity(self, description: str, technologies: List[str], 
                                   project: Dict) -> float:
        """Calculate similarity between current project and historical project"""
        # Text similarity
        desc_words = set(description.lower().split())
        project_desc = project.get("description", "") or project.get("project_name", "")
        project_words = set(project_desc.lower().split())
        
        text_similarity = len(desc_words & project_words) / max(len(desc_words | project_words), 1)
        
        # Technology similarity
        project_techs = project.get("technologies", [])
        if isinstance(project_techs, str):
            project_techs = [project_techs]
        
        tech_similarity = 0.0
        if technologies and project_techs:
            tech_set1 = set(tech.lower() for tech in technologies)
            tech_set2 = set(tech.lower() for tech in project_techs)
            tech_similarity = len(tech_set1 & tech_set2) / max(len(tech_set1 | tech_set2), 1)
        
        # Combined similarity
        return (text_similarity * 0.6) + (tech_similarity * 0.4)
    
    def calculate_confidence(self, estimate: ProjectEstimate) -> float:
        """Calculate confidence level for the estimate"""
        confidence = 0.8  # Base confidence
        
        # Reduce confidence based on complexity
        confidence -= (estimate.complexity_score - 0.5) * 0.3
        
        # Reduce confidence based on risk
        confidence -= estimate.risk_score * 0.2
        
        # Increase confidence if we have similar projects
        if len(estimate.similar_projects) > 2:
            confidence += 0.1
        
        # Reduce confidence for new technologies
        new_tech_count = sum(1 for tech in estimate.technologies 
                           if self.tech_complexity.get(tech, 0.5) > 0.7)
        confidence -= new_tech_count * 0.05
        
        return max(0.3, min(0.95, confidence))
    
    def analyze_tech_complexity(self, technologies: List[str]) -> Dict:
        """Analyze technology complexity breakdown"""
        if not technologies:
            return {}
        
        analysis = {}
        
        for tech in technologies:
            complexity = self.tech_complexity.get(tech, 0.5)
            
            analysis[tech] = {
                "complexity": complexity,
                "difficulty": self.get_difficulty_level(complexity),
                "learning_curve": self.knowledge_base.get("technology_learning_curves", {}).get(tech, 0.5),
                "category": self.get_tech_category(tech)
            }
        
        return analysis
    
    def get_difficulty_level(self, complexity: float) -> str:
        """Convert complexity score to difficulty level"""
        if complexity < 0.3:
            return "Easy"
        elif complexity < 0.6:
            return "Medium"
        elif complexity < 0.8:
            return "Hard"
        else:
            return "Expert"
    
    def get_tech_category(self, technology: str) -> str:
        """Get category for a technology"""
        for category, techs in self.skill_categories.items():
            if technology in techs:
                return category
        return "other"
    
    def export_estimate(self, estimate: ProjectEstimate, format: str = "json") -> str:
        """Export estimate in various formats"""
        if format == "json":
            return self.export_estimate_json(estimate)
        elif format == "report":
            return self.export_estimate_report(estimate)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def export_estimate_json(self, estimate: ProjectEstimate) -> str:
        """Export estimate as JSON"""
        data = {
            "project_name": estimate.project_name,
            "created_at": estimate.created_at.isoformat(),
            "total_hours": estimate.total_hours,
            "optimistic_hours": estimate.optimistic_hours,
            "realistic_hours": estimate.realistic_hours,
            "pessimistic_hours": estimate.pessimistic_hours,
            "complexity_score": estimate.complexity_score,
            "difficulty_level": estimate.difficulty_level,
            "confidence_level": estimate.confidence_level,
            "risk_score": estimate.risk_score,
            "risk_factors": estimate.risk_factors,
            "technologies": estimate.technologies,
            "tech_complexity": estimate.tech_complexity,
            "recommended_team_size": estimate.recommended_team_size,
            "recommended_roles": estimate.recommended_roles,
            "team_members": estimate.team_members,
            "phase_breakdown": estimate.phase_breakdown,
            "skill_breakdown": estimate.skill_breakdown,
            "similar_projects": estimate.similar_projects
        }
        
        return json.dumps(data, indent=2, default=str)
    
    def export_estimate_report(self, estimate: ProjectEstimate) -> str:
        """Export estimate as readable report"""
        report = f"""
PROJECT ESTIMATION REPORT
========================

Project: {estimate.project_name}
Generated: {estimate.created_at.strftime('%Y-%m-%d %H:%M')}

SUMMARY
-------
Total Estimated Hours: {estimate.total_hours}
  • Optimistic: {estimate.optimistic_hours} hours
  • Realistic: {estimate.realistic_hours} hours  
  • Pessimistic: {estimate.pessimistic_hours} hours

Complexity: {estimate.difficulty_level} ({estimate.complexity_score:.1%})
Confidence: {estimate.confidence_level:.1%}
Risk Score: {estimate.risk_score:.1%}

TEAM RECOMMENDATIONS
-------------------
Team Size: {estimate.recommended_team_size} people
Roles: {', '.join(estimate.recommended_roles)}

Recommended Team Members:
"""
        
        for member in estimate.team_members:
            report += f"  • {member['name']} - {member['role']} (${member['hourly_rate']}/hr)\n"
        
        report += f"""
TECHNOLOGY ANALYSIS
------------------
Technologies: {', '.join(estimate.technologies)}

Technology Complexity:
"""
        
        for tech, analysis in estimate.tech_complexity.items():
            report += f"  • {tech}: {analysis['difficulty']} (complexity: {analysis['complexity']:.1%})\n"
        
        if estimate.risk_factors:
            report += "\nRISK FACTORS\n------------\n"
            for risk in estimate.risk_factors:
                report += f"  • {risk['description']} (impact: {risk['impact']:.1%})\n"
        
        if estimate.phase_breakdown:
            report += "\nPHASE BREAKDOWN\n---------------\n"
            for phase, info in estimate.phase_breakdown.items():
                report += f"  • {phase.title()}: {info['hours']} hours ({info['percentage']:.0f}%)\n"
        
        if estimate.similar_projects:
            report += "\nSIMILAR PROJECTS\n----------------\n"
            for proj in estimate.similar_projects[:3]:
                report += f"  • {proj['name']} (similarity: {proj['similarity']:.1%})\n"
        
        return report

# Test the project estimator
if __name__ == "__main__":
    # Mock data source manager
    class MockDataManager:
        def get_team_members(self):
            return [
                {
                    "name": "John Doe",
                    "skills": ["react", "javascript", "css", "frontend"],
                    "hourly_rate": 75,
                    "availability": "available",
                    "experience": "5 years"
                },
                {
                    "name": "Jane Smith", 
                    "skills": ["python", "django", "postgresql", "backend"],
                    "hourly_rate": 85,
                    "availability": "available",
                    "experience": "7 years"
                }
            ]
        
        def get_all_projects(self):
            return [
                {
                    "project_name": "E-commerce Website",
                    "technologies": ["react", "node.js", "postgresql"],
                    "estimated_hours": 160,
                    "actual_hours": 180,
                    "status": "completed"
                }
            ]
    
    # Test estimation
    print("🧪 Testing Project Estimator...")
    
    estimator = ProjectEstimator(MockDataManager())
    
    # Test project estimation
    description = "Build a responsive e-commerce website using React and Node.js with payment integration"
    requirements = [
        "User authentication and registration",
        "Product catalog with search",
        "Shopping cart functionality", 
        "Stripe payment integration",
        "Admin dashboard for inventory management"
    ]
    technologies = ["react", "node.js", "express", "postgresql", "stripe"]
    
    estimate = estimator.estimate_project(description, requirements, technologies)
    
    print(f"✅ Project: {estimate.project_name}")
    print(f"✅ Estimated Hours: {estimate.total_hours}")
    print(f"✅ Difficulty: {estimate.difficulty_level}")
    print(f"✅ Team Size: {estimate.recommended_team_size}")
    print(f"✅ Confidence: {estimate.confidence_level:.1%}")
    print(f"✅ Similar Projects: {len(estimate.similar_projects)}")
    
    # Test export
    json_export = estimator.export_estimate(estimate, "json")
    print(f"✅ JSON Export: {len(json_export)} characters")
    
    print("✅ Project Estimator test completed!")