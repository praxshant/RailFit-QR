import numpy as np
from datetime import datetime, timedelta

class RailwayAIAnalyzer:
    def analyze_item_performance(self, item_data):
        insights = {
            'quality_score': self._calculate_quality_score(item_data),
            'maintenance_prediction': self._predict_maintenance(item_data),
            'risk_assessment': self._assess_risks(item_data),
            'recommendations': []
        }
        insights['recommendations'] = self._generate_recommendations(insights)
        return insights

    def _calculate_quality_score(self, item_data):
        inspection_dates = item_data.get('inspection_dates', [])
        if len(inspection_dates) == 0:
            return {'score': 50, 'status': 'No inspections recorded'}
        days_since_last = self._days_since_last_inspection(inspection_dates)
        if days_since_last < 30:
            score = 95
        elif days_since_last < 90:
            score = 80
        elif days_since_last < 180:
            score = 65
        else:
            score = 40
        return {
            'score': score,
            'status': self._get_status_from_score(score),
            'days_since_inspection': days_since_last
        }

    def _predict_maintenance(self, item_data):
        supply_date_str = item_data.get('supply_date')
        try:
            supply_date = datetime.fromisoformat(supply_date_str) if supply_date_str else datetime.now()
        except Exception:
            supply_date = datetime.now()
        days_in_service = (datetime.now() - supply_date).days
        item_type = item_data.get('item_type', '')
        maintenance_intervals = {
            'elastic_rail_clip': 365,
            'rail_pad': 730,
            'liner': 1095,
            'sleeper': 1825
        }
        interval = maintenance_intervals.get(item_type, 365)
        next_maintenance = supply_date + timedelta(days=interval)
        days_until = (next_maintenance - datetime.now()).days
        return {
            'next_maintenance_date': next_maintenance.isoformat(),
            'days_until_maintenance': max(0, days_until),
            'urgency': 'High' if days_until < 30 else 'Medium' if days_until < 90 else 'Low'
        }

    def _assess_risks(self, item_data):
        risks = []
        warranty_period = item_data.get('warranty_period', '') or ''
        if isinstance(warranty_period, str) and 'expired' in warranty_period.lower():
            risks.append('Warranty expired - increased failure risk')
        inspection_dates = item_data.get('inspection_dates', [])
        if len(inspection_dates) == 0:
            risks.append('No inspection history - unknown condition')
        return {
            'risk_level': 'High' if len(risks) > 1 else 'Medium' if len(risks) == 1 else 'Low',
            'identified_risks': risks
        }

    def _generate_recommendations(self, insights):
        recommendations = []
        if insights['quality_score'].get('score', 0) < 60:
            recommendations.append('Schedule immediate inspection')
        if insights['maintenance_prediction']['urgency'] == 'High':
            recommendations.append('Plan maintenance within 30 days')
        if insights['risk_assessment']['risk_level'] == 'High':
            recommendations.append('Consider replacement or intensive monitoring')
        return recommendations

    def _days_since_last_inspection(self, inspection_dates):
        if not inspection_dates:
            return 999
        try:
            last = inspection_dates[-1]
            last_dt = datetime.fromisoformat(last)
        except Exception:
            return 999
        return (datetime.now() - last_dt).days

    def _get_status_from_score(self, score):
        if score >= 90:
            return 'Excellent'
        elif score >= 75:
            return 'Good'
        elif score >= 60:
            return 'Fair'
        else:
            return 'Poor'
