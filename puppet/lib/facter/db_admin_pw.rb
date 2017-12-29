# db_admin_pw.rb
Facter.add('db_admin_pw') do
   setcode '/bin/cat /opt/scos-sensor/.db_admin_pw'
end
