# db_superuser.rb
Facter.add('db_superuser') do
   setcode '/bin/cat /opt/scos/.db_superuser'
end
