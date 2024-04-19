# Slack and Teams Notifier
Simple package for sending logger-like messages to Slack and Microsoft Teams.

### Install
```bash
pip install git+https://github.com/tenJnd/notifier.git@main

```

### Usage - Example
```python
from slack_bot.notifications import SlackNotifier, TeamsNotifier

# Generate URLs (in how-to section)
# Slack example: 'https://hooks.slack.com/services/T01Rku4T5LZ/j02JrBK8U14/oPD9PuzYfeBXdhmFAvWMV8sR'
# Teams example: '<URL_TEAMS>'
url_slack = '<SLACK_URL>'
url_teams = '<TEAMS_URL>'

# Initialize notifier with URL, name and username are optional
slack_notifier = SlackNotifier(url=url_slack, name=__name__, username='pipeline')
teams_notifier = TeamsNotifier(url=url_teams, name=__name__, username='pipeline')

if __name__ == "__main__":
    slack_notifier.info('This is an info message')
    slack_notifier.warning('This is a warning message')
    slack_notifier.error('This is an error message with echo', echo="here") # echo adds @here to the message

    teams_notifier.info('This is an info message')
    teams_notifier.warning('This is a warning message')
    teams_notifier.error('This is an error message')
```
Message params:
- **echo (str, list)**: Can be set to mention a specific person or the whole channel. If you want to mention a specific person, add the person's email address prefix (before @). For example, **firstname.lastname@email.com** would be **echo='firstname.lastname'**. You can mention multiple persons using a list: **echo=['firstname.lastname', 'firstname.lastname']**.

### Example Notifications
![img_1.png](img_1.png)

## How to Generate SLACK_URL
**In Slack go to**: 
`Browse -> Apps -> search for "Incoming WebHooks" -> Configuration -> Add to Slack -> choose channel -> add Incoming WebHooks integration`
**DONE!**

## How to Generate TEAMS_URL
**In Microsoft Teams**:
Follow the instructions provided by Microsoft Teams for generating an incoming webhook URL for your channel.
