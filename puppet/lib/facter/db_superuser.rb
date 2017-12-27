# db_superuser.rb
Facter.add('db_superuser') do
   setcode '/bin/cat /opt/scos-sensor/.db_superuser'
end
