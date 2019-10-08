#  -*- coding: utf-8 -*-
"""
Sample script to return current date/time in required formats.
Copyright (c) 2016-2019 Cisco and/or its affiliates.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from datetime import datetime

def curr_dtf():
    '''Define current date and time for Filenames'''
    ft = datetime.now().strftime('%Y%m%d-%H%M%S')
    return(ft)

def curr_dtl():
    '''Define current date and time for logging'''
    lt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return(lt)

def main():
    print(curr_dtf())
    print(curr_dtl())

if __name__ == "__main__":
    main()
