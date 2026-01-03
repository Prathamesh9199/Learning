+-------------------+---------------------------------------------------+
|  NL 2 SQL Agent   |  Session: [ session_user_1 ]   (Reset) (Load)     |
+-------------------+---------------------------------------------------+
|  Sessions         |                                                   |
|  > session 1      |               [User]                              |
|  > session 2      |               Why is cost high for Project Alpha? |
| > current session |                                                   |
|                   |                                                   |
|                   |  [Sherlock]                                       |
|                   |  [Thinking ..] (this block is accordian)          |
|                   |   ! > LIVE LOGS                       !           |
|                   |   ! ------------------------------    !           |
|                   |   ! Intent: DIAGNOSTIC                !           |
|                   |   ! Planner: Querying KG...           !           |
|                   |   ! Graph: Found 'Location'           !           |
|                   |   ! Planner: Testing Hyp...           !           |
|                   |   ! Exec: sp_GetDist...               !           |
|                   |   ! Analyzer: High variance           !           |
|                   |                                                   |
|                   |  I'm investigating. I found that **Location** is  |
|                   |  the primary driver.                              |
|                   |                                                   |
|                   |  Here is the breakdown by Location:               |
|                   |                                                   |
|                   |  +------------+------------+                      |
|                   |  | Location   | Cost       |                      |
|                   |  +------------+------------+                      |
|                   |  | India      | $50,000    |                      |
+-------------------+  | USA        | $120,000   |                      |
|   User Profile    |  +------------+------------+                      |
|  > Settings       |                                                   |
|  > Log out        |  It seems USA costs are 2.4x higher.              |
|                   |                                                   |
|                   +---------------------------------------------------+
|                   | [ Type your message...                          ] |
+-------------------+---------------------------------------------------+