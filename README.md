# Zoom-Analytics-API

Over the past 9 months I've been working in an intermittent freelance capacity for a company performing analytics on events they've been running over Zoom. I developed code to transform raw Zoom logs into visualizations and tables describing individual and cumulative participation. I beleive these analytics can be useful to almost any business that uses Zoom frequently, so I decided to take all of my work and package it into a web app that's extremely simple to use. I created a flask API that receives Zoom logs from a user, and turns the logs into a page of metrics, including:
<ul>
<li> A table with each individual participant, their first login to the meeting, their last logout from the meeting, and the total amount of time they spent in the meeting.</li>
<li>The meeting’s peak attendance, and the time at which that peak took place.</li>
<li>A visualization of meeting attendance, with the number of active participants plotted at every single minute from the start to the end of the meeting. The graph also has a dotted line of average attendance throughout.
The meeting’s total attendance.</li>
<li>A visualization of cumulative attendance, with the amount of people that had joined the meaning by/at each minute plotted from start to finish.</li>
</ul>

The second feature I developed was a username cleaning service. By far, the thing I spend the most time on while working with zoom logs is fixing usernames. The two biggest problems are people using different names over the course of the meeting -- obviously we would want to merge these for accurate overall attendance and accurate times for those participants -- and people using names that didn’t match the name they used to register for the event. I was able to leverage all those meticulous hours in order to tailor the cleaning software to the most common inconsistencies and errors. First I set up a filter to catch similar usernames using three different Levenshtein distance calculations, and formatted each pair into a radio group where the user could choose to merge A into B, B into  A, or neither. Additionally, using a combination of the .isalpha() function, which looks for non-letter characters, and subsequent regex matches to check if the non-letter characters aligned with common name conventions, such as First Hyphenated-Last or First M. Last, in which case the name wouldn’t be brought to the user’s attention. Names that failed all of these tests are flagged as poorly formatted and are presented to the user as a text input group, with the option to type in a replacement for that name. Once the user has confirmed that they have selected or inputted all the changes they want to make, the app generates a downloadable .json file which, when uploaded to the main page in tandem with a zoom logs file, performs all of these substitutions before creating the table and visualizations on the metrics page. 

I designed the app such that it never actually saves any uploaded file. It reads the file, extracts the information, and passes that information to a new page, losing the original file upon redirection. The information the app gleans will also be gone the instant the user closes or leaves that page. I did this for the security and stability of the app, the security of the user’s data, and the fact that I didn’t need to implement third-party cloud storage. This design choice forced me to solve some complex problems, but I feel it was worth it in the end. Zoom Analytics is probably one of the lone web apps that only take information explicitly given by the user, and only keep that information for as long as necessary, and not a second more.

## See it in action: ## 
https://zoom-analytics-api.herokuapp.com/



### V1.1 4/14/21 ### 
<ul><li>Table on the metrics page can now be downloaded</li></ul>
