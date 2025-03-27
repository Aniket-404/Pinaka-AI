from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class NotificationForm(FlaskForm):
    monitored_objects = StringField('Objects to Monitor (comma-separated)', 
                                   validators=[DataRequired()],
                                   default='person,car,dog,cat,bicycle,laptop,cell phone,Movement')
    confidence_threshold = FloatField('Confidence Threshold', 
                                     validators=[DataRequired(), NumberRange(min=0, max=1)],
                                     default=0.7)
    submit = SubmitField('Save Settings') 