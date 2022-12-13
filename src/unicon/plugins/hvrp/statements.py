"""
Module:
    unicon.plugins.hvrp
Authors:
    Miguel Botia (mibotiaf@cisco.com), Leonardo Anez (leoanez@cisco.com)
Description:
     Module for defining all the Statements and callback required for the
    Current implementation
"""
from unicon.core.errors import UniconAuthenticationError
from unicon.eal.dialogs import Statement
from unicon.plugins.hvrp.patterns import HvrpPatterns
from unicon.plugins.generic.statements import pre_connection_statement_list, \
    login_handler, user_access_verification, \
    password_handler, bad_password_handler, \
    incorrect_login_handler, get_enable_credential_password

pat = HvrpPatterns()


#############################################################
#  Hvrp statements
#############################################################


def enable_password_handler(spawn, context, session):
    enable_credential_password = get_enable_credential_password(context=context)
    if enable_credential_password:
        spawn.sendline(enable_credential_password)
    else:
        spawn.sendline(context['enable_password'])


class HvrpStatements(object):
    """
        Class that defines All the Statements for Hvrp platform
        implementation
    """

    def __init__(self):
        '''
         All hvrp Statements
        '''

        self.bad_password_stmt = Statement(pattern=pat.bad_passwords,
                                           action=bad_password_handler,
                                           args=None,
                                           loop_continue=False,
                                           continue_timer=False)

        self.login_incorrect = Statement(pattern=pat.login_incorrect,
                                         action=incorrect_login_handler,
                                         args=None,
                                         loop_continue=True,
                                         continue_timer=False)

        self.login_stmt = Statement(pattern=pat.username,
                                    action=login_handler,
                                    args=None,
                                    loop_continue=True,
                                    continue_timer=False)
        self.useraccess_stmt = Statement(pattern=pat.useracess,
                                         action=user_access_verification,
                                         args=None,
                                         loop_continue=True,
                                         continue_timer=False)
        self.password_stmt = Statement(pattern=pat.password,
                                       action=password_handler,
                                       args=None,
                                       loop_continue=True,
                                       continue_timer=False)
        self.save_config_notice = Statement(pattern=r'(\[y\/n\])|(\[Y\/N\])',
                                            action=lambda
                                                spawn: spawn.sendline('y'),
                                            args=None,
                                            loop_continue=True,
                                            continue_timer=False)

        self.super_prompt = Statement(pattern=r'^.*[Pp]assword:',
                                              action=enable_password_handler,
                                              args=None,
                                              loop_continue=True,
                                              continue_timer=False)

#############################################################
#  Statement lists
#############################################################

hvrp_statements = HvrpStatements()

#############################################################
# Authentication Statements
#############################################################

authentication_statement_list = [hvrp_statements.bad_password_stmt,
                                 hvrp_statements.login_incorrect,
                                 hvrp_statements.login_stmt,
                                 hvrp_statements.useraccess_stmt,
                                 hvrp_statements.password_stmt
                                 ]

connection_statement_list = authentication_statement_list + \
                            pre_connection_statement_list

default_statement_list = [hvrp_statements.save_config_notice, hvrp_statements.super_prompt]
