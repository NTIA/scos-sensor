# Scripts

## data_download.sh

1. ssh into the sensor using a known user account: `ssh [username]@[sensor IP]`
1. Note/copy password from `.admin_password` file:
   `cat /opt/scos-sensor/.admin_password`
1. Open a web browser and navigate to the sensor browsable API: `http://[sensor IP]`.
   Log in using the `admin` account, and the password from above
1. Once logged in, click on "users" link
1. Note/copy the "auth_token"
1. Go back to main page and click on the "schedule" link
1. Note/copy all the schedule "name"/s and the corresponding "next_task_id"
1. Run `data_download.sh` and follow the prompts
1. When prompted for the "Last file to copy", subtract 1 from the "next_task_id" value
   above
