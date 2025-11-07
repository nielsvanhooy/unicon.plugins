""" Generic IOS-XE Service Statements """

__author__ = "Myles Dear <pyats-support@cisco.com>"

from unicon.eal.dialogs import Statement
from .patterns import IosXEPatterns, FactoryResetPatterns
from unicon.plugins.generic.statements import chatty_term_wait

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#
#           Service handlers
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


def send_response(spawn, response=""):
    chatty_term_wait(spawn)
    spawn.sendline(response)


patterns = IosXEPatterns()


overwrite_previous = Statement(pattern=patterns.overwrite_previous,
                               action='sendline()',
                               loop_continue=True,
                               continue_timer=False)

delete_filename = Statement(pattern=patterns.delete_filename,
                            action='sendline()',
                            loop_continue=True,
                            continue_timer=False)

confirm = Statement(pattern=patterns.confirm_prompt,
                    action='sendline()',
                    loop_continue=True,
                    continue_timer=False)

are_you_sure = Statement(pattern=patterns.are_you_sure,
                         action='sendline(y)',
                         loop_continue=True,
                         continue_timer=False)

are_you_sure_ywtdt = Statement(pattern=patterns.are_you_sure_ywtdt,
                               action='sendline(yes)',
                               loop_continue=True,
                               continue_timer=False)

wish_continue = Statement(pattern=patterns.wish_continue,
                          action='sendline(yes)',
                          loop_continue=True,
                          continue_timer=False)

want_continue = Statement(pattern=patterns.want_continue,
                          action='sendline(yes)',
                          loop_continue=True,
                          continue_timer=False)

press_enter = Statement(pattern=patterns.press_enter,
                        action='sendline()',
                        loop_continue=True,
                        continue_timer=False)

do_you_want_to = Statement(pattern=patterns.do_you_want_to,
                           action='sendline(y)',
                           loop_continue=True,
                           continue_timer=False)

proceed_confirm_stmt = Statement(pattern=patterns.proceed_confirm,
                                 action='sendline(yes)',
                                 loop_continue=True,
                                 continue_timer=False)

accept_eula_stmt = Statement(pattern=patterns.accept_uela,
                             action='sendline(yes)',
                             loop_continue=True,
                             continue_timer=False)

reload_eula_prompt_stmt = Statement(pattern=patterns.uela_reload_prompt,
                             action='sendline(yes)',
                             loop_continue=True,
                             continue_timer=False)




macro_prompt = Statement(pattern=patterns.macro_prompt,
                         loop_continue=False)

dest_file_startup = Statement(pattern=patterns.dest_file_startup,
    action="sendline()",
    loop_continue=True,
    continue_timer=False)


configure_statement_list = [
    are_you_sure,
    wish_continue,
    confirm,
    want_continue,
    are_you_sure_ywtdt,
    proceed_confirm_stmt,
    accept_eula_stmt,
    macro_prompt,
    reload_eula_prompt_stmt
]

execute_statement_list = [
    dest_file_startup,
    overwrite_previous,
    delete_filename,
    confirm,
    want_continue,
    do_you_want_to,
    accept_eula_stmt,
    reload_eula_prompt_stmt
]

#############################################################################
# Factory Reset Command Statement
#############################################################################
pat = FactoryResetPatterns()


factory_reset_confirm = Statement(pattern=pat.factory_reset_confirm,
                        action=send_response, args={'response': ''},
                        loop_continue=True,
                        continue_timer=False)

are_you_sure_confirm = Statement(pattern=pat.are_you_sure_confirm,
                        action=send_response, args={'response': ''},
                        loop_continue=True,
                        continue_timer=False)