# MATE ROV Announcements Bot
A Discord bot built on [discord.py](https://github.com/Rapptz/discord.py) which scrapes the MATE ROV competition [website](https://materovcompetition.org/) for competition updates and notifies subscribed Discord servers
## Usage
Click this [link](https://discord.com/api/oauth2/authorize?client_id=1049374366875521065&permissions=2147534848&scope=bot%20applications.commands) to invite the bot to your discord server.
### Commands
`/subscribe [page] [channel]`  
Subscribe a channel to page update notifications for one page. Valid pages are `explorer`, `pioneer`, `ranger`, `navigator`, `scout`, `scoring`, and `worlds`. If no channel is specified the channel from which you called the command will be used as the default.

`/unsubscribe [page] [channel]`  
Remove a single subscription with the specified page name from the specified channel

`/unsubscribe all`  
Removes all subscription from all channels in the current server

`/list`  
List all subscriptions for the current server
