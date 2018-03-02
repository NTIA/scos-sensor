# postgres_password.rb
Facter.add('postgres_password') do
   setcode '/bin/cat /opt/scos-sensor/.postgres_password'
end
