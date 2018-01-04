# db_admin_email.rb
Facter.add('db_admin_email') do
   setcode '/bin/cat /opt/scos-sensor/.db_admin_email'
end
