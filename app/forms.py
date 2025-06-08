from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, NumberRange, Optional

class NotificationForm(FlaskForm):
    monitored_objects = StringField('Objects to Monitor (comma-separated)', 
                                   validators=[DataRequired()],
                                   default='stone,gas_cylinder,Movement,person,car')
    confidence_threshold = FloatField('Confidence Threshold', 
                                     validators=[DataRequired(), NumberRange(min=0, max=1)],
                                     default=0.7)
    
    # SMS notification settings
    sms_enabled = BooleanField('Enable SMS Notifications', default=False)
    sms_objects = StringField('Objects for SMS Alerts (comma-separated)',
                             validators=[Optional()],
                             default='person,car,stone,gas_cylinder')
    sms_cooldown = IntegerField('SMS Cooldown (seconds)',
                               validators=[Optional(), NumberRange(min=10, max=3600)],
                               default=60)
    
    submit = SubmitField('Save Settings')